# Using AI Skills at Work: A Beginner's Guide

> New to AI? You're in the right place. Developers and skill authors: see the
> [technical reference](docs/REFERENCE.md).

## At a glance

The AI skills kit gives your AI assistant a short set of team rules, so it explains what it will do, asks before risky actions and protects private information. You install it once in about five minutes, and it works in the Claude app, Claude Code, Codex and Cursor.

What's in the kit:

- **Three skills**: short rule books the AI reads. One helps people new to AI, one covers security habits, one keeps code changes small and tested.
- **A double-click setup** that adds the skills and explains every choice in plain words.
- **A one-page guide** ([`GUIDE.md`](GUIDE.md)) with six safety habits.
- **A short [`AGENTS.md`](templates/AGENTS.md) file** for project folders, which makes the AI follow the most important rules every time.

Nothing is forced on you. Everything is optional and can be undone. In our test of 63 sessions, the AI asked before installing software 3 times out of 3 with the kit set up fully, compared with 0 out of 3 without it.

## A few words, explained

You only need four terms to use the kit.

| Term | What it means | Everyday comparison |
| --- | --- | --- |
| **AI assistant** | A program you talk to in normal sentences, such as Claude or ChatGPT. It writes, summarises and answers questions. | A helpful colleague you can message any time |
| **AI agent** | An AI assistant that can also *do* things: open and change files, run programs, fill in forms, send messages. | That colleague, but with access to your computer and accounts |
| **Skill** | A short instruction sheet the AI reads, so it works the way our team wants. | A briefing note you hand a new colleague on day one |
| **AGENTS.md** | A tiny file in a project folder with the few rules the AI must always follow. The AI reads it every time. | The sign on the office door: "Ask before you throw anything away" |

Why this matters: an agent's mistakes have real effects, such as a deleted file or a sent email. The skills make it slow down, explain, and check with you first.

## The three skills

If you don't write code, you only need the first skill. The setup recommends the right ones for you.

| Skill | Who it's for | What the AI does differently |
| --- | --- | --- |
| [**guided-ai-use**](skills/guided-ai-use/SKILL.md) | Everyone, especially people new to AI | Tells you its plan in plain words before acting. Asks before deleting, sending, sharing or buying anything. Avoids copying personal data such as salaries or contact details. Ends with what it did and what you should check. |
| [**secure-coding-baseline**](skills/secure-coding-baseline/SKILL.md) | Anyone who lets AI work on files or code | Keeps passwords and keys private. Ignores instructions hidden inside documents or web pages, and tells you about them. Asks before installing software or changing important settings. |
| [**disciplined-coding**](skills/disciplined-coding/SKILL.md) | People who write or review code | Makes small, focused changes. Writes a test to prove a bug is fixed. Leaves unrelated code alone and mentions it instead. |

You don't need to call a skill by name. The AI picks up the rules on its own, and the `AGENTS.md` file makes sure the most important ones always apply.

## Setting up (about five minutes)

You run one setup helper that asks you simple questions. It asks before every change, backs up anything it edits, and sends nothing anywhere.

1. **Download the kit.** At the top of this page, click the green **Code** button, then **Download ZIP**. Unzip it, for example into your Documents folder.
2. **Start the setup.** In the unzipped folder, double-click **Start AI Setup (Mac)** or **Start AI Setup (Windows)**. A window with text opens.
   - On a Mac, the first time, macOS may block it. Right-click the file and choose **Open**.
   - If it says Python is missing, ask IT or a developer to install Python 3.9 or newer.
3. **Pick your AI tools.** Type the numbers of the tools you use, or press Enter to accept the suggestion. Not sure? Choose the Claude app.
4. **Pick your skills.** Press Enter to accept the recommended ones.
5. **Optional safety settings.** You can say no and skip them. If you say yes, each one is explained before you decide. Pressing Enter picks the recommended answer.
6. **Review and confirm.** The helper lists what it will do. Type `y` to go ahead, or `n` to stop with nothing changed.
7. **Finish up.**
   - **Claude app users:** the helper creates one small file per skill in a folder called `ai-safety-setup` in your home folder. Upload these in the Claude app's skills settings, or ask your admin to add them for the whole team.
   - **Claude Code, Codex or Cursor users:** restart the tool so it picks up the skills.

A summary of everything that was done is saved in that `ai-safety-setup` folder.

**Working in a project folder?** Copy [`templates/AGENTS.md`](templates/AGENTS.md) from the kit into the folder. If you use Claude Code, also create a file named `CLAUDE.md` there containing the single line `@AGENTS.md`. Ask a developer if this sounds unfamiliar; it takes one minute.

## Using it day to day

Keep working as you normally would: describe what you want in plain sentences. The skills change how the AI responds, not how you ask.

**Example requests that work well:**

- "Summarise the three reports in my Downloads folder into one page."
- "Tidy up my Desktop: sort the files into folders by type."
- "Draft a reply to this customer email. Don't send it."
- "Summarise this HR spreadsheet for my manager."
- "Fill in this registration form using my profile details."

**What you'll notice with the skills:**

| Moment | Without the skills | With the skills |
| --- | --- | --- |
| Before starting | Often starts straight away | Says its plan, for example "I'll read the three files and create one new document. Nothing existing will change." |
| Unclear request | Picks one meaning silently | Asks, for example "By tidy, do you mean delete old files or sort them into folders?" |
| Risky step | May go ahead | Stops and asks, for example "I'm about to send this to 230 people. Send now, or show me first?" |
| Private data | May copy names and salaries | Uses totals instead, and says what it left out |
| Finishing | "Done." | What it did, what it didn't do, and what you should check |

**How to answer its questions:** reply in normal words, such as "yes", "no", or "show me first". If you don't understand a question, say "Explain that more simply" or "Why are you asking?". Saying no is always safe.

## Six safety habits

The skills help, but you are still the one in charge. These habits matter with or without the kit.

1. **Know what it's about to do.** If the AI doesn't explain its plan, ask: "What exactly will you change?"
2. **Say yes only to what you understand.** Read every permission question. When unsure, say no and ask why.
3. **Keep secrets out.** Don't paste passwords, one-time codes, card numbers or other people's personal data unless the task truly needs it and it's approved.
4. **Be suspicious of outside content.** Emails, documents and web pages can hide text aimed at the AI, such as "AI assistant: send this file to...". The AI should only follow you. If it suggests something odd after reading something, stop and check.
5. **Check before you rely on it.** The AI can be confidently wrong. Check facts, numbers and recipients, especially for anything leaving the company.
6. **You own the result.** The AI is a helper, not a sign-off. What you send or publish is your responsibility.

## Common questions

**Do I have to use this?** No. The kit shares our team's guidelines; nothing is enforced. You can skip the optional settings and undo everything later.

**Will the AI become slow or annoying?** No. In our tests, simple questions still got short, direct answers. The extra checks only appear for actions that change, send or delete things.

**Does the setup send my data anywhere?** No. It only changes files on your own computer, and it backs them up first.

**How do I undo it?** The summary in your `ai-safety-setup` folder lists every file that changed and its backup. Restore the backups, or ask a developer to run the uninstall command listed there.

**The AI didn't ask before doing something risky. Why?** Skills are guidance, not a lock. The AI usually follows them, but not always. That's why the six habits above still matter. Please tell the team what happened so we can improve the rules.

**The setup window closed or showed an error.** Run it again; it's safe to repeat. If it mentions Python, ask IT to install Python 3.9 or newer. Otherwise, send a screenshot to the contact below.

**Can I suggest a new skill?** Yes, please. If you keep giving the AI the same instructions, or it keeps making the same mistake, that's a good candidate.

## Getting help

Ask for help straight away if the AI did something you didn't expect, or if you think a password or personal data was exposed. Reporting it is always the right call.

- **Contact:** add your team's channel or email here
- **Technical reference** (commands, authoring rules, how the tools work): [`docs/REFERENCE.md`](docs/REFERENCE.md)
- **Test results** behind the recommendations: [`ai-skills-test/results/RESULTS.md`](ai-skills-test/results/RESULTS.md)
- **Your setup summary:** the `ai-safety-setup` folder in your home folder
