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
            Free emails until subscription starts: <strong>${c.user.num_remaining}</strong>
        </p>
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
