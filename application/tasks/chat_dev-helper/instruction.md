# Developer Coding-Help Chatbot

Your Python script crashes with **`KeyError: 'name'`** on the line
**`value = data['user']['name']`**. It works for most records, but some `user` records don't
have a nested `name` field.

Your goal: get a **working fix** so the missing field no longer crashes the script, and
understand **why** it happened.

- Describe the problem and, when asked, share the language (Python), the exact error, and the
  failing line.
- Get a concrete fix (e.g. a safe lookup / default) and a short explanation you can act on.

Chat as yourself — the assigned persona — a terse senior dev and a confused beginner should
sound very different. Keep going until you have a fix you can apply.
