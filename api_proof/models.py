
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='api_app_user_set',
        related_query_name='api_app_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='api_app_user_set',
        related_query_name='api_app_user',
    )
    
    def __str__(self):
        return self.email

class CardanoWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    name = models.CharField(max_length=100, blank=True, null=True)
    payment_address = models.CharField(max_length=120, unique=True)
    stake_address = models.CharField(max_length=120, unique=True, blank=True, null=True)
    payment_signing_key = models.TextField()
    payment_verification_key = models.TextField()
    stake_signing_key = models.TextField()
    stake_verification_key = models.TextField()
    network = models.CharField(max_length=20, default='mainnet')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read_only = models.BooleanField(default=False)  
    
    def __str__(self):
        read_only = " (lecture seule)" if self.is_read_only else ""
        return f"{self.name}{read_only} - {self.payment_address}"   

class CardanoTransaction(models.Model):
    TRANSACTION_STATUS = [
        ('pending', 'En attente'),
        ('submitted', 'Soumise'),
        ('confirmed', 'Confirmée'),
        ('failed', 'Échouée')
    ]
    
    wallet = models.ForeignKey(CardanoWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_hash = models.CharField(max_length=64, unique=True)
    from_address = models.CharField(max_length=120)
    to_address = models.CharField(max_length=120)
    amount_ada = models.DecimalField(max_digits=20, decimal_places=6)
    amount_lovelace = models.BigIntegerField()
    fee_lovelace = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='submitted')
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_hash[:16]}... - {self.amount_ada} ADA"