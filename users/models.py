from django.db import models
# from PIL import Image
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser, UserManager


class CustomUserManager(UserManager):
    def _create_user(self, name, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(name, email, password, **extra_fields)

    def create_superuser(self, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(name, email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=30, unique=False)
    name = models.CharField(max_length=20)
    email = models.EmailField(
        ('email address'),
        max_length=255,
        unique=True,
        help_text=('Required. Your unique email address is used for authentication.'),
        error_messages={
            'unique': ("A user with that email already exists."),
        },
    )

    
    USERNAME_FIELD = 'email'  # Removes the username field in favour of email
    REQUIRED_FIELDS = ['name', ]

    objects = CustomUserManager()

    def __str__(self):
        return str(self.id)


class Portal(models.Model):
    name = models.CharField(max_length=10, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name



# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     image = models.ImageField(default='default.jpg', upload_to='profile_pics')
#     stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
#     one_click_purchasing = models.BooleanField(default=False)
#     created_on = models.DateTimeField(auto_now=True)

#     orders = models.ManyToManyField(
#         'index.Product', blank=True, related_name="products_owned")
#     wishlist = models.ManyToManyField(
#         'index.Product', blank=True, related_name='wishlist')
#     price_tracking = models.ManyToManyField(
#         'index.Product', blank=True, related_name='price_tracking')

#     def __str__(self):
#         return f"{self.user.username} Profile"

#     # # over-riding save method to scale down user image
#     # def save(self, *args, **kwargs):
#     #     super().save(*args, **kwargs)

#     #     img = Image.open(self.image.path)

#     #     if img.height > 300 or img.width > 300:
#     #         output_size = (300, 300)
#     #         img.thumbnail(output_size)
#     #         img.save(self.image.path)


# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()

