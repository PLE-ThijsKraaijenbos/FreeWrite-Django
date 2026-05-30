import cloudinary.uploader

from .models import Post, PostLike


class PostService:
    @staticmethod
    def get_post_list():
        return Post.objects.order_by('-created_at')

    @staticmethod
    def create_post(*, author, title, body, image=None) -> Post:
        image_url = None
        if image:
            result = cloudinary.uploader.upload(image, folder='community/posts', resource_type='image')
            image_url = result['secure_url']
        return Post.objects.create(author=author, title=title, body=body, image_url=image_url)

    @staticmethod
    def like_post(*, user, post: Post) -> None:
        PostLike.objects.get_or_create(user=user, post=post)

    @staticmethod
    def unlike_post(*, user, post: Post) -> None:
        PostLike.objects.filter(user=user, post=post).delete()
