<%
    cfg = context.get("config")
    views_and_triggers = bool(cfg) and (
        (cfg.get_main_option("views_and_triggers") or "").lower() == "true"
    )
%>"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
% if views_and_triggers:
from triggers import create_triggers, drop_triggers
from views import create_views, drop_views
% endif
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}
% if views_and_triggers:

# ukrdc_resources_database commit SHA (or release tag) the views are built from.
# None keeps the previous revision's views.
VIEWS_REF = None
% endif


def upgrade():
% if views_and_triggers:
    drop_triggers()
    drop_views(down_revision, revision)

    ${upgrades if upgrades else "# no schema changes"}

    create_views(revision)
    create_triggers()  # update_date trigger on any new table
% else:
    ${upgrades if upgrades else "pass"}
% endif


def downgrade():
% if views_and_triggers:
    drop_triggers()
    drop_views(revision, down_revision)

    ${downgrades if downgrades else "# no schema changes"}

    create_views(down_revision)
    create_triggers()
% else:
    ${downgrades if downgrades else "pass"}
% endif
