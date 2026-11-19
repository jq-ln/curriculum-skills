# Releasing the Template

The Template is released with release-please like any Derived repo, as [`docs/workflow/releases.md`](../docs/workflow/releases.md) says. Init deletes this file, with the rest of `.template/`.

## Commit types

A Template PR's type says what it means for Derived repos, not which files it touches, so the Template's changelog tells Derived repos what to adopt:

| Type | Use it for |
| --- | --- |
| `feat` | A new or changed inherited convention, script or workflow. |
| `feat!` | A change that makes existing Derived repos change how they work. Add the `BREAKING CHANGE:` footer saying what they change. |
| `fix` | A correction to inherited content. |
| `docs` | Template-own docs, such as `.template/` and the landing page, or an edit that changes nothing for Derived repos. |

So a new job in `ci.yml` is `feat`, not `ci`, because every Derived repo inherits it. In a Derived repo, each type keeps its ordinary Conventional Commits meaning; [`commits.md`](../docs/workflow/commits.md#pr-title) lists the types.
