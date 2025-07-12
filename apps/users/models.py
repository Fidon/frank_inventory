from django.db import models
from apps.shops.models import Shop
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, username, fullname, shop, phone=None, password=None, is_admin=False, **extra_fields):
        if not username:
            raise ValueError(_("The username field cannot be blank"))
        if not fullname:
            raise ValueError(_("The fullname field cannot be blank"))
        if not shop:
            raise ValueError(_("The shop field cannot be blank."))

        # Normalize username by converting to lowercase and stripping whitespace
        username = username.lower().strip()
        fullname = fullname.strip()

        # Set default password if not provided
        if password is None:
            password = username.upper()  # Default password is username in capital letters

        user = self.model(
            username=username,
            fullname=fullname,
            phone=phone if phone else None,
            shop=shop,
            is_admin=is_admin,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, fullname, shop, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(
            username=username,
            fullname=fullname,
            phone=phone,
            shop=shop,
            password=password,
            **extra_fields
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Phone number validator
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,13}$',
        message=_("Invalid phone number format.")
    )

    # Username validator (only alphabets a-zA-Z)
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z]+$',
        message=_("Only alphabets allowed.")
    )

    # Primary key
    id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID")
    )

    # User credentials
    username = models.CharField(
        unique=True,
        max_length=32,
        validators=[username_validator],
        verbose_name=_("Username"),
        help_text=_("Required. 32 characters or fewer. Only alphabets (a-zA-Z).")
    )

    fullname = models.CharField(
        max_length=255,
        verbose_name=_("Full Name"),
        help_text=_("The user's full name")
    )

    phone = models.CharField(
        max_length=13,
        validators=[phone_validator],
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Phone Number"),
        help_text=_("User's phone number in international format")
    )

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Shop"),
        help_text=_("The shop this user belongs to.")
    )

    last_login = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Last Login"),
        help_text=_("Date and time of the user's last login")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Designates whether this user account is active (not blocked).")
    )

    is_admin = models.BooleanField(
        default=False,
        verbose_name=_("Admin Status"),
        help_text=_("Designates whether the user has admin privileges")
    )

    deleted = models.BooleanField(
        default=False,
        verbose_name=_("Deleted"),
        help_text=_("Designates whether this user has been deleted")
    )

    # Additional information
    comment = models.TextField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Comment"),
        help_text=_("Additional notes about the user")
    )

    # Timestamps for tracking changes
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Date and time when the user was created")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Date and time when the user was last updated")
    )

    # Many-to-many relationships
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='custom_users',
        verbose_name=_("Groups"),
        help_text=_("The groups this user belongs to. A user will get all permissions "
                   "granted to each of their groups.")
    )

    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='custom_users',
        verbose_name=_("User Permissions"),
        help_text=_("Specific permissions for this user.")
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname', 'shop']

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = 'customuser'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['fullname']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active', 'deleted']),
            models.Index(fields=['shop']),
        ]

    def __str__(self):
        return str(self.fullname if self.fullname else self.username)

    def clean(self):
        super().clean()
        
        # Clean and format username
        if self.username:
            self.username = self.username.strip()
            if self.username:
                self.username = self.username[0].upper() + self.username[1:].lower()
            else:
                self.username = None

        # Clean and format fullname
        if self.fullname:
            names = self.fullname.strip().split(' ')
            cleaned_names = []
            for name in names:
                if name:
                    cleaned_names.append(name[0].upper() + name[1:].lower())
            self.fullname = ' '.join(cleaned_names) if cleaned_names else None
        else:
            self.fullname = None

        # Set phone and comment to None if blank
        self.phone = self.phone.strip() if self.phone else None
        self.comment = self.comment.strip() if self.comment else None

        # Ensure is_superuser is False unless explicitly set by create_superuser
        if not self.is_admin:
            self.is_superuser = False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


