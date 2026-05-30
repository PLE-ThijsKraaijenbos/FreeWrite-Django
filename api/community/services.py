from .models import Post, PostLike


class PostService:
    @staticmethod
    def get_post_list():
        return Post.objects.order_by('-id')

    @staticmethod
    def like_post(*, user, post: Post) -> None:
        PostLike.objects.get_or_create(user=user, post=post)

    @staticmethod
    def unlike_post(*, user, post: Post) -> None:
        PostLike.objects.filter(user=user, post=post).delete()
