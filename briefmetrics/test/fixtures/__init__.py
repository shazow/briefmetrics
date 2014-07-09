from briefmetrics import api

def populate_dev():
    user = api.account.get_or_create(
        email=u'shazow@gmail.com',
        display_name=u'Andrey Petrov',
        is_admin=True,
    )

    remote_data = {
        u'id': u'76827151',
        u'accountId': u'407051',
        u'internalWebPropertyId': u'74397951',
        u'name': u'All Web Site Data',
        u'timezone': u'America/Los_Angeles',
        u'webPropertyId': u'UA-407051-16',
        u'websiteUrl': u'http://www.briefmetrics.com',
    }

    api.report.create(
        account_id=user.accounts[0].id,
        subscribe_user_id=user.id,
        remote_data=remote_data,
    )
