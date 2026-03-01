import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings


def send_otp_email(email, otp):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email}],
        sender={"email": "info.medcoreai@gmail.com"},
        subject="Your MedCore AI OTP",
        html_content=f"<h2>Your OTP is: {otp}</h2>"
    )

    try:
        # ⭐ DEBUG PRINT START
        response = api_instance.send_transac_email(send_smtp_email)

        print("\n===== BREVO RESPONSE =====")
        print(response)
        print("OTP SENT TO:", email)
        print("==========================\n")
        # ⭐ DEBUG PRINT END

        return True

    except ApiException as e:
        print("\n===== BREVO ERROR =====")
        print(e)
        print("=======================\n")
        return False
