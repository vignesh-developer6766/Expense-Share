from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.group_service import GroupService

groups_bp = Blueprint("groups", __name__, url_prefix="/groups")


@groups_bp.route("")
@groups_bp.route("/")
@login_required
def list_groups():
    user_groups = GroupService.get_user_groups(current_user.id)
    return render_template("groups/list.html", groups=user_groups)


@groups_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Group name is required.", "danger")
            return render_template("groups/create.html", name=name, description=description)

        group = GroupService.create_group(name=name, description=description, creator_id=current_user.id)
        flash(f"Group '{group.name}' created successfully!", "success")
        return redirect(url_for("groups.group_detail", group_id=group.id))

    return render_template("groups/create.html")


@groups_bp.route("/<int:group_id>")
@login_required
def group_detail(group_id):
    if not GroupService.is_member(group_id, current_user.id):
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("groups.list_groups"))

    group = GroupService.get_group_by_id(group_id)
    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for("groups.list_groups"))

    return render_template("groups/detail.html", group=group)


@groups_bp.route("/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
def edit_group(group_id):
    if not GroupService.is_member(group_id, current_user.id):
        flash("You are not a member of this group.", "danger")
        return redirect(url_for("groups.list_groups"))

    group = GroupService.get_group_by_id(group_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Group name is required.", "danger")
            return render_template("groups/edit.html", group=group)

        success, message = GroupService.update_group(group_id, name, description, current_user.id)
        if success:
            flash(message, "success")
            return redirect(url_for("groups.group_detail", group_id=group.id))
        else:
            flash(message, "danger")

    return render_template("groups/edit.html", group=group)


@groups_bp.route("/<int:group_id>/delete", methods=["POST"])
@login_required
def delete_group(group_id):
    success, message = GroupService.delete_group(group_id, current_user.id)
    if success:
        flash(message, "success")
        return redirect(url_for("groups.list_groups"))
    else:
        flash(message, "danger")
        return redirect(url_for("groups.group_detail", group_id=group_id))


@groups_bp.route("/<int:group_id>/members/add", methods=["POST"])
@login_required
def add_member(group_id):
    if not GroupService.is_member(group_id, current_user.id):
        flash("Unauthorized action.", "danger")
        return redirect(url_for("groups.list_groups"))

    email = request.form.get("email", "").strip()
    if not email:
        flash("Please enter an email address.", "danger")
        return redirect(url_for("groups.group_detail", group_id=group_id))

    success, message = GroupService.add_member_by_email(group_id, email)
    if success:
        flash(message, "success")
    else:
        flash(message, "warning")

    return redirect(url_for("groups.group_detail", group_id=group_id))


@groups_bp.route("/<int:group_id>/members/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_member(group_id, user_id):
    success, message = GroupService.remove_member(group_id, user_id, current_user.id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("groups.group_detail", group_id=group_id))
