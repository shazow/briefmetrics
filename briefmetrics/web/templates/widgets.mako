<%def name="nav(items, current_route=None)">
    <ul class="nav">
        % for label, href in items:
            % if current_route == href:
        <li class="active">
            % else:
        <li>
            % endif
            <a href="${href}">${label}</a>
        </li>
        % endfor
    </ul>
</%def>

<%def name="flash_messages(messages)">
% if messages:
    <div class="flash-messages container">
        <ul class="ping">
        % for m in messages:
            <li>${m}</li>
        % endfor
        </ul>
    </div>
% endif
</%def>


<%def name="plan_summary(payment, num_remaining)">
% if payment:
    % if payment.is_charging and num_remaining:
        <p>
            Free emails until subscription starts: <strong>${c.user.num_remaining}</strong>
        </p>
    % elif not payment.is_charging:
        % if num_remaining:
        <p>
            Free emails until trial ends: <strong>${c.user.num_remaining}</strong>
        </p>
        % endif
        <ul>
            <li>
                <a class="highlight" href="${request.route_path('api', _query={
                    'method': 'settings.payments_set',
                    'format': 'redirect',
                    'next': request.route_path('settings'),
                    'csrf_token': session.get_csrf_token(),
                })}">Activate Subscription</a>
                % if num_remaining:
                    to continue receiving reports after the trial.
                % else:
                    to resume your reports.
                % endif
            </li>
        </ul>
    % endif
% elif num_remaining:
    <p>
        Free emails remaining: <strong>${num_remaining}</strong>
    </p>

    <ul>
        <li>
            <a class="highlight" href="/settings#credit-card">Add a credit card</a>
            to upgrade your account.
        </li>
    </ul>
% elif num_remaining is not None:
    <p>
        <a class="highlight" href="/settings#credit-card">Add a credit card</a>
        to upgrade your account and resume your reports.
    </p>
% else:
    <p>
        You are the proud owner of a free Briefmetrics account. Please enjoy thoroughly. :)
    </p>
% endif
</%def>

<%def name="login_cta(login_url)">
    <a class="cta" href="${login_url}">
        <button>Sign in with Google Analytics</button>
        <small>get your first email report now</small>
    </a>
</%def>

