<%def name="flash_messages(messages)">
% if messages:
    <div class="flash-messages">
        <ul>
        % for m in messages:
            <li>${m}</li>
        % endfor
        </ul>
    </div>
% endif
</%def>


<%def name="plan_summary(has_card, num_remaining)">
% if has_card:
    % if num_remaining:
        <p>
            Free reports until subscription starts: <strong>${c.user.num_remaining}</strong>
        </p>
    % else:
        <p>
            $8 per month.
        </p>
    % endif
    <ul>
        <li>
            <a href="/settings?method=settings.payments_cancel&csrf_token=${session.get_csrf_token()}" onclick="return confirm('Are you sure you want to cancel your Briefmetrics subscription?');">Cancel subscription</a>
        </li>
    </ul>
% elif num_remaining:
    <p>
        Free reports remaining: <strong>${num_remaining}</strong>
    </p>

    <ul>
        <li>
            <a class="highlight" href="/settings#credit-card" onclick="$('#credit-card').slideDown(); return false;">Add a credit card</a>
            to upgrade your account.
        </li>
        <li>
            $8/mo subscription starts only after your free reports run out.
        </li>
        <li>
            When you upgrade, your remaining free reports are doubled!
        </li>
    </ul>
% elif num_remaining is not None:
    <p>
        <a class="highlight" href="/settings#credit-card" onclick="$('#credit-card').slideDown(); return false;">Add a credit card</a>
        to upgrade your account and start your $8/mo subscription to resume reports.
    </p>
% else:
    <p>
        You are the proud owner of a free Briefmetrics account. Please enjoy responsibly. :)
    </p>
% endif
</%def>
