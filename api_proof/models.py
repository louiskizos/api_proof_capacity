
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
    



class CardanoNFT(models.Model):
    NFT_TYPES = [
        ('certification', 'Certification'),
        ('art', 'Art'),
        ('collectible', 'Collectible'),
        ('utility', 'Utility'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('minted', 'Minté'),
        ('received', 'Reçu'),
        ('sent', 'Envoyé'),
        ('burned', 'Brûlé'),
    ]
    
    wallet = models.ForeignKey(CardanoWallet, on_delete=models.CASCADE, related_name='nfts')
    policy_id = models.CharField(max_length=255, db_index=True)
    asset_name = models.CharField(max_length=255, db_index=True)
    fingerprint = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict)
    nft_type = models.CharField(max_length=20, choices=NFT_TYPES, default='certification')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cardano_nfts'
        unique_together = ['policy_id', 'asset_name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.policy_id[:10]}...)"
    
    @property
    def asset_id(self):
        return f"{self.policy_id}{self.asset_name}"

class CertificationNFT(models.Model):
    
    nft = models.OneToOneField(CardanoNFT, on_delete=models.CASCADE, related_name='certification')
    issuer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_certifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_certifications')
    certification_type = models.CharField(max_length=100)
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    verification_url = models.URLField(blank=True)
    is_revoked = models.BooleanField(default=False)
    revocation_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'certification_nfts'
    
    def __str__(self):
        return f"Certification {self.certification_type} - {self.recipient.username}"

class NFTPolicy(models.Model):
    """Politique de minting pour NFTs"""
    POLICY_TYPES = [
        ('single_issuer', 'Émetteur unique'),
        ('multi_issuer', 'Multi-émetteurs'),
        ('time_locked', 'Verrouillé temporel'),
    ]
    
    name = models.CharField(max_length=200)
    policy_id = models.CharField(max_length=255, unique=True)
    policy_script = models.TextField()  # Script CBOR
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, default='single_issuer')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_policies')
    valid_before = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'nft_policies'
    
    def __str__(self):
        return f"Policy {self.name} ({self.policy_id[:10]}...)"




class VideoCourse(models.Model):

    COURSE_LEVELS = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    level = models.CharField(max_length=20, choices=COURSE_LEVELS, default='beginner')
    duration_hours = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    thumbnail_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'video_courses'
    
    def __str__(self):
        return self.title

class VideoModule(models.Model):

    course = models.ForeignKey(VideoCourse, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField()  # Lien vers la vidéo
    duration_minutes = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)  # Gratuit en preview
    
    class Meta:
        db_table = 'video_modules'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class CourseEnrollment(models.Model):

    ENROLLMENT_STATUS = [
        ('active', 'Actif'),
        ('completed', 'Terminé'),
        ('dropped', 'Abandonné'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(VideoCourse, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='active')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.FloatField(default=0)
    
    class Meta:
        db_table = 'course_enrollments'
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title}"

class VideoView(models.Model):

    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='video_views')
    module = models.ForeignKey(VideoModule, on_delete=models.CASCADE)
    watch_duration_seconds = models.PositiveIntegerField(default=0)
    watched_percentage = models.FloatField(default=0)
    last_watched_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'video_views'
        unique_together = ['enrollment', 'module']
    
    def __str__(self):
        return f"{self.enrollment.student.email} - {self.module.title}"

class Quiz(models.Model):

    module = models.ForeignKey(VideoModule, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.FloatField(default=70)  # Score minimum en %
    max_attempts = models.PositiveIntegerField(default=3)
    
    class Meta:
        db_table = 'quizzes'
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

class QuizQuestion(models.Model):

    QUESTION_TYPES = [
        ('multiple_choice', 'Choix multiple'),
        ('true_false', 'Vrai/Faux'),
        ('short_answer', 'Réponse courte'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'quiz_questions'
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}..."

class QuestionOption(models.Model):

    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'question_options'
    
    def __str__(self):
        return f"{self.text[:30]}... (Correct: {self.is_correct})"

class QuizAttempt(models.Model):

    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    answers_data = models.JSONField(default=dict)  # Stocke les réponses
    
    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.enrollment.student.email} - {self.quiz.title}: {self.score}%"

class VideoCourseCertificate(models.Model):

    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, related_name='certificate')
    nft = models.ForeignKey('CardanoNFT', on_delete=models.SET_NULL, null=True, blank=True, related_name='video_certificates')
    issued_at = models.DateTimeField(auto_now_add=True)
    skills_verified = models.JSONField(default=list)  # Compétences vérifiées
    
    class Meta:
        db_table = 'video_course_certificates'
    
    def __str__(self):
        return f"Certificat: {self.enrollment.course.title} - {self.enrollment.student.email}"
    





