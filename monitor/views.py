from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Keyword, Flag
from .serializers import KeywordSerializer, FlagSerializer
from .services import run_scan


class KeywordView(APIView):
    def post(self, request):
        serializer = KeywordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScanView(APIView):
    def post(self, request):
        result = run_scan()
        return Response({
            'message': 'Scan complete',
            'flags_created': result['created'],
            'flags_skipped_suppressed': result['skipped']
        })


class FlagListView(APIView):
    def get(self, request):
        flags = Flag.objects.all().order_by('-score')
        serializer = FlagSerializer(flags, many=True)
        return Response(serializer.data)


class FlagDetailView(APIView):
    def patch(self, request, pk):
        try:
            flag = Flag.objects.get(pk=pk)
        except Flag.DoesNotExist:
            return Response({'error': 'Flag not found'}, status=status.HTTP_404_NOT_FOUND)

        allowed = ['pending', 'relevant', 'irrelevant']
        new_status = request.data.get('status')

        if new_status not in allowed:
            return Response(
                {'error': f'Status must be one of: {allowed}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        flag.status = new_status
        flag.save()
        return Response(FlagSerializer(flag).data)
from django.shortcuts import render

class LoginPageView(APIView):
    def get(self, request):
        return render(request, 'login_page.html')