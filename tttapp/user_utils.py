
# -----------------------------------------

from django.contrib import messages
from django.shortcuts import render

from django_ratelimit.exceptions import Ratelimited


def rate_limit_exceeded(request, exception):
    if isinstance(exception, Ratelimited):
        messages.error(
            request,
            "You have exceeded the rate limit for this action.\nPlease try again later.",
        )
        return render(request, "429.html", status=429)
    return render(request, "403.html", status=403)


# -----------------------------------------

# Custom rate function
def rate(group, request):
    if request.user.is_authenticated:
        rate = "1000/m"
    else:
        rate = "3/m"
    print("Rate:", rate)
    return rate


# -----------------------------------------
