<%inherit file="base.mako"/>

<p>
    Google Analytics returned no results for your site: ${c.report.report.display_name}
</p>

<p>
    If your site is brand new, then no worries. Briefmetrics will try again in a few weeks when there is more data available.
</p>


<h2>Troubleshooting</h2>

<p>
    Do you see any data in
    <a href="${h.ga_permalink('report/content-pages', c.report.report)}">your Google Analytics report here</a>?
</p>

<ol>
    <li>
        If you do, then that means Briefmetrics is broken somehow. Please reply to this email for further support. :)
    </li>
    <li>
        If all the charts are flat, then it could mean one of two things:
        <ul>
            <li>
                Your website is not wired up with Google Analytics correctly. You can check
                <a href="${h.ga_permalink('management/Settings', c.report.report)}/%3Fm.page%3DTrackingCode/">your Tracking Code status and instructions here</a>.
            </li>
            <li>
                No one has visited your website this week. :( If you reply to this email, I'd love to check it out!
            </li>
        </ul>
    </li>
</ol>

<p>
    If you have other sites you wanted to try Briefmetrics on, you can
    <a href="https://briefmetrics.com/reports">change your subscription</a>.
    Or if this isn't looking like the right tool for you, no hard feelings if you
    <a href="https://briefmetrics.com/account/delete?token=${c.user.unsubscribe_token}">delete your account</a>.
</p>

<p>
    Sincerely,<br />
    Andrey and his army of code collectively known as Briefmetrics
</p>
