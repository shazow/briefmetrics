from briefmetrics import api

def populate_dev():
    user = api.account.get_or_create(
        email=u'shazow@gmail.com',
        display_name=u'Andrey Petrov',
        is_admin=True,
    )

    report = api.report.create(
        account_id=user.account.id,
        subscribe_user_id=user.id,
        remote_id=u'76827151',
        display_name=u'briefmetrics.com',
    )
