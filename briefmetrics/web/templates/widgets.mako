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
