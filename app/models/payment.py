from datetime import datetime, timezone
from enum import Enum as PyEnum
from app.extensions import db


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class PaymentStatus(PyEnum):
    """Enumeration for payment status values."""
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'


class Payment(db.Model):
    """Payment model for Paystack transaction records."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reference = db.Column(db.String(100), unique=True, nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)  # Amount in pesewas (smallest currency unit)
    currency = db.Column(db.String(3), default='GHS', nullable=False)
    status = db.Column(
        db.Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    paystack_id = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        """Serialize payment to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reference': self.reference,
            'amount': self.amount,
            'amount_display': self.amount / 100,  # Convert pesewas to cedis for display
            'currency': self.currency,
            'status': self.status.value if self.status else None,
            'paystack_id': self.paystack_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Payment {self.reference}>'
