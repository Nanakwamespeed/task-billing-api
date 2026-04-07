from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Payment
from app.models.payment import PaymentStatus
from app.routes import payments_bp
from app.services.paystack import PaystackService
from app.utils import paginate_query, generate_reference, success_response, error_response


@payments_bp.route('/initialize', methods=['POST'])
@jwt_required()
def initialize_payment():
    """
    Initialize a new payment via Paystack
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - amount
          properties:
            amount:
              type: number
              example: 100.50
              description: Amount in GHS (cedis)
            description:
              type: string
              example: Payment for project consultation
            currency:
              type: string
              default: GHS
              example: GHS
    responses:
      200:
        description: Payment initialized successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Payment initialized successfully
            data:
              type: object
              properties:
                reference:
                  type: string
                  example: TASKBILL-ABC123DEF456
                authorization_url:
                  type: string
                  example: https://checkout.paystack.com/xxx
                access_code:
                  type: string
                  example: abc123def456
                payment_id:
                  type: integer
                  example: 1
      400:
        description: Validation error or Paystack error
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))

    if not user:
        return error_response('User not found', status_code=404)

    data = request.get_json()

    if not data:
        return error_response('Request body is required', status_code=400)

    amount = data.get('amount')
    if amount is None:
        return error_response('Amount is required', errors={'amount': 'Amount is required'}, status_code=400)

    try:
        amount = float(amount)
        if amount <= 0:
            return error_response('Amount must be greater than 0', errors={'amount': 'Amount must be positive'}, status_code=400)
    except (TypeError, ValueError):
        return error_response('Invalid amount', errors={'amount': 'Amount must be a number'}, status_code=400)

    description = data.get('description', '').strip() or None
    currency = data.get('currency', 'GHS').upper()

    if currency not in ['GHS', 'NGN', 'USD']:
        return error_response('Invalid currency', errors={'currency': 'Must be one of: GHS, NGN, USD'}, status_code=400)

    reference = generate_reference()

    paystack = PaystackService()
    result = paystack.initialize_transaction(
        email=user.email,
        amount_ghs=amount,
        reference=reference,
        description=description
    )

    if not result['success']:
        return error_response(result.get('message', 'Failed to initialize payment'), status_code=400)

    payment = Payment(
        user_id=user.id,
        reference=reference,
        amount=int(amount * 100),
        currency=currency,
        status=PaymentStatus.PENDING,
        description=description
    )

    db.session.add(payment)
    db.session.commit()

    return success_response(
        'Payment initialized successfully',
        data={
            'reference': result['reference'],
            'authorization_url': result['authorization_url'],
            'access_code': result['access_code'],
            'payment_id': payment.id
        }
    )


@payments_bp.route('/verify/<reference>', methods=['GET'])
@jwt_required()
def verify_payment(reference):
    """
    Verify a payment transaction via Paystack
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - in: path
        name: reference
        type: string
        required: true
        description: Payment reference
    responses:
      200:
        description: Payment verified
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Payment verified successfully
            data:
              type: object
              properties:
                status:
                  type: string
                  example: success
                payment:
                  type: object
      400:
        description: Verification failed
      404:
        description: Payment not found
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    payment = Payment.query.filter_by(
        reference=reference,
        user_id=int(current_user_id)
    ).first()

    if not payment:
        return error_response('Payment not found', status_code=404)

    if payment.status == PaymentStatus.SUCCESS:
        return success_response(
            'Payment already verified',
            data={
                'status': 'success',
                'payment': payment.to_dict()
            }
        )

    paystack = PaystackService()
    result = paystack.verify_transaction(reference)

    if not result['success']:
        return error_response(result.get('message', 'Verification failed'), status_code=400)

    if result['status'] == 'success':
        payment.status = PaymentStatus.SUCCESS
        payment.paystack_id = result.get('paystack_id')
        message = 'Payment verified successfully'
    else:
        payment.status = PaymentStatus.FAILED
        message = 'Payment verification failed'

    db.session.commit()

    return success_response(
        message,
        data={
            'status': payment.status.value,
            'payment': payment.to_dict()
        }
    )


@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Paystack webhook events
    ---
    tags:
      - Payments
    parameters:
      - in: header
        name: X-Paystack-Signature
        type: string
        required: true
        description: Paystack webhook signature
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            event:
              type: string
              example: charge.success
            data:
              type: object
    responses:
      200:
        description: Webhook processed successfully
      400:
        description: Invalid signature or payload
    """
    signature = request.headers.get('X-Paystack-Signature')
    payload = request.get_data()

    paystack = PaystackService()

    if not paystack.verify_webhook_signature(payload, signature):
        return error_response('Invalid signature', status_code=400)

    data = request.get_json()

    if not data:
        return error_response('Invalid payload', status_code=400)

    event = data.get('event')
    event_data = data.get('data', {})

    if event == 'charge.success':
        reference = event_data.get('reference')
        if reference:
            payment = Payment.query.filter_by(reference=reference).first()
            if payment and payment.status != PaymentStatus.SUCCESS:
                payment.status = PaymentStatus.SUCCESS
                payment.paystack_id = str(event_data.get('id', ''))
                db.session.commit()

    return success_response('Webhook received')


@payments_bp.route('', methods=['GET'])
@jwt_required()
def get_payments():
    """
    Get all payments for the authenticated user
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [pending, success, failed]
        description: Filter by payment status
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        default: 10
        description: Items per page (max 100)
    responses:
      200:
        description: Payments retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Payments retrieved successfully
            data:
              type: array
              items:
                type: object
            meta:
              type: object
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    query = Payment.query.filter_by(user_id=int(current_user_id))

    status = request.args.get('status')
    if status:
        try:
            status_enum = PaymentStatus(status)
            query = query.filter_by(status=status_enum)
        except ValueError:
            return error_response(f'Invalid status: {status}', status_code=400)

    query = query.order_by(Payment.created_at.desc())

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 10)

    payments, meta = paginate_query(query, page, per_page)

    return success_response(
        'Payments retrieved successfully',
        data=payments,
        meta=meta
    )


@payments_bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """
    Get a single payment by ID
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - in: path
        name: payment_id
        type: integer
        required: true
        description: Payment ID
    responses:
      200:
        description: Payment retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Payment retrieved successfully
            data:
              type: object
      404:
        description: Payment not found
      401:
        description: Unauthorized
    """
    current_user_id = get_jwt_identity()

    payment = Payment.query.filter_by(
        id=payment_id,
        user_id=int(current_user_id)
    ).first()

    if not payment:
        return error_response('Payment not found', status_code=404)

    return success_response(
        'Payment retrieved successfully',
        data=payment.to_dict()
    )
