from django.contrib.auth.models import User
from django.http import Http404

from main.api.genericViews.auth import AuthRequiredView
from main.api.paginations.custom import CustomPagination
from main.api.serializers.users import UserMoreInfoSerializer


class UserBaseView(AuthRequiredView):
    paginator_class = CustomPagination()
    serializer_class = UserMoreInfoSerializer
    model_class = User

    def get_query_list(self, request):
        username = request.GET.get("q", "")

        if username or len(username) >= 3:
            obj = self.model_class.objects.filter(username__contains=username)
        else:
            obj = self.model_class.objects.exclude(is_active=True)

        paginated_user = self.paginator_class.paginate_queryset(obj, request)
        serializer = self.serializer_class(paginated_user, many=True, context={"user": request.user})

        return serializer.data

    def get_query(self, pk):
        try:
            obj = self.model_class.objects.get(id=pk)
        except User.DoesNotExist:
            raise Http404

        return obj