maily
propose: Let's build "maily", a local console, CLI-style, application which simplifies my handling of email accounts. For MVP/v1 it will only handle gmail, hence all client references will be regarding "gmail", but may apply to other email providers (eg: microsoft outlook/hotmail, custom email provider, corporate email, etc) in the future. The app should ask for authentication once and securely store credentials, re-requesting user auth whenever neccesary. Whenever inference/LLM is needed, local Ollama shall be used, (to be configured if not available at startup); examples of inference needed may be examining/categorizing/summarizing email subject+body contents. Configuration shall live in the user's home directory under the ".maily/" folder.
Flows:
1. Daily, maily should fetch all unread emails and split them by category. 
  1. If there's any new email in the spam folder, list it and ask for deletion or not-spam confirmation from the user.
    1. If any email from the spam folder is flagged for deletion, or as "not spam" by the user, delete it or send it to the inbox accordingly.
  1. If any unread email from the inbox appears to be spam not caught by gmail rules, display them in a list, asking user for confirmation on which to flag.
    1. If any of said emails are confirmed to be spam by the user, create a rule so gmail correctly filters them from now on, and send them to the spam folder. Emails not flagged by the user as spam at this point should continue in the inbox, unread, for next steps.
  1. Group and count all remaining unread emails from the inbox into categories, then display the list of categories, each with a number of "unread (new today) | unread (previously existing) | read" items.
    1. "Categories" here are completely separated from gmail folder/tags/flags; those can be brought 
    1. If a "Category" for where to fit certain emails does not exist, list as "Other". Upon reviewing this "Other" category contents, maily may propose the user proper names to classify them
    1. There should be a simple configuration file which stores the list of category names and the simple static-analysis script and/or inference rules to be ran per-email in order to sort them into said categories. Default configuration should invoke local Ollama running `gemma4:e2b`. Inference may be slow and/or expensive, so everything that may be determined by static analysis should be.
    1. "Categories" must always include the following:
        - "Action Required": all emails which require an action on the part of the user (account verification code, password expiration notice, invoice expiration notice, other due dates..)
        - "Personal": all emails written by humans to the sender, as long as they are not strictly job-related
        - "Work": all emails written by humans to the sender, which are clearly about work-related matters for ongoing projects
        - "Work proposals": all emails written by humans to the sender, which are clearly about work-related matters for new projects. These may also include non-human generated emails that would otherwise fall into "job search" category, if they are specifically tailored to the user's profile and their areas of expertise and appear to be about a real oportunity
        - "Job search": all emails coming from newsletters, job boards, etc, which may contain job oportunities which may or may not appeal to the user's profile/experience/interests
        - "Newsletters - techincal"
        - "Newsletters - other"
        - "Other"
1. User should simply be able to navigate expand/collapse the list of emails per category, pagination is out of scope for now
1. Each received email may fit into more than 1 category, we are still to decide how to display/filter/count/summarize coherently
1. User should simply be able to sort the list of emails of each category by different criteria (arrival date of first email in thread, arrival date of last email in thread, inferred importance/urgency, by sender names, by sender email domain)
1. User should simply be able to request summary/digest and/or recommended actions per category and per email.

> "Inbox" should consider all unread emails outside of the spam folder, not caring whether they have already been filtered by gmail into any folder/tag/etc

gmail API reference can be found at: https://developers.google.com/workspace/gmail/api/reference/rest

"maily" executable should check installation of gmail CLI (if needed) and/or any other tools and their configuration at every launch, silently (only reporting errors requiring human action) by default, may be changed as requested by a config flag.

Undecided if flows should be one-shot text-output (user calls from terminal, maily responds with a single text response and action suggestions and finishes) or interactive TUI (or both?). In "text-output" mode a "-json-format" tag should be provided so the cli's output is formatted as JSON instead of pretty-formated ascii-art-tables/markdown for human consumption.

Tech stack TBD: may be minimal .Net or Python. Ideally group of scripts that run from a folder, installation being as simple as copying the script-holding folder and adding it to system path, and configuration migration being as simple as moving the `.maily` folder in the user's home.

Ask me any questions so we can refine the specs before beginning with implementation.