from app.extensions import db
from app.models.group import Group, GroupMember
from app.models.user import User


class GroupService:
    @staticmethod
    def create_group(name: str, description: str, creator_id: int) -> Group:
        group = Group(name=name.strip(), description=description.strip() if description else "", created_by=creator_id)
        db.session.add(group)
        db.session.flush()

        # Creator is automatically added as a member
        membership = GroupMember(group_id=group.id, user_id=creator_id)
        db.session.add(membership)
        db.session.commit()
        return group

    @staticmethod
    def get_user_groups(user_id: int):
        return (
            Group.query.join(GroupMember, Group.id == GroupMember.group_id)
            .filter(GroupMember.user_id == user_id)
            .order_by(Group.created_at.desc())
            .all()
        )

    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        return db.session.get(Group, group_id)

    @staticmethod
    def is_member(group_id: int, user_id: int) -> bool:
        return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first() is not None

    @staticmethod
    def add_member_by_email(group_id: int, email: str) -> tuple[bool, str]:
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            return False, f"No registered user found with email '{email}'."

        existing_membership = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
        if existing_membership:
            return False, f"{user.name} is already a member of this group."

        membership = GroupMember(group_id=group_id, user_id=user.id)
        db.session.add(membership)
        db.session.commit()
        return True, f"Added {user.name} to the group."

    @staticmethod
    def remove_member(group_id: int, user_id_to_remove: int, current_user_id: int) -> tuple[bool, str]:
        group = db.session.get(Group, group_id)
        if not group:
            return False, "Group not found."

        # Only creator or self can remove member
        if group.created_by != current_user_id and user_id_to_remove != current_user_id:
            return False, "You do not have permission to remove this member."

        membership = GroupMember.query.filter_by(group_id=group_id, user_id=user_id_to_remove).first()
        if not membership:
            return False, "User is not a member of this group."

        # Creator cannot be removed if other members exist
        if user_id_to_remove == group.created_by and len(group.members) > 1:
            return False, "Group creator cannot be removed while other members exist."

        db.session.delete(membership)
        db.session.commit()
        return True, "Member removed successfully."

    @staticmethod
    def update_group(group_id: int, name: str, description: str, current_user_id: int) -> tuple[bool, str]:
        group = db.session.get(Group, group_id)
        if not group:
            return False, "Group not found."

        if not GroupService.is_member(group_id, current_user_id):
            return False, "Unauthorized access."

        group.name = name.strip()
        group.description = description.strip() if description else ""
        db.session.commit()
        return True, "Group updated successfully."

    @staticmethod
    def delete_group(group_id: int, current_user_id: int) -> tuple[bool, str]:
        group = db.session.get(Group, group_id)
        if not group:
            return False, "Group not found."

        if group.created_by != current_user_id:
            return False, "Only the group creator can delete this group."

        db.session.delete(group)
        db.session.commit()
        return True, "Group deleted successfully."
