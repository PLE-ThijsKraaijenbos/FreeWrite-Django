from .models import Post, PostLike


class PostService:
    @staticmethod
    def get_post_list():
        return Post.objects.order_by('-created_at')

    @staticmethod
    def create_post(*, author, title, body) -> Post:
        return Post.objects.create(author=author, title=title, body=body)

    @staticmethod
    def like_post(*, user, post: Post) -> None:
        PostLike.objects.get_or_create(user=user, post=post)

    @staticmethod
    def unlike_post(*, user, post: Post) -> None:
        PostLike.objects.filter(user=user, post=post).delete()
