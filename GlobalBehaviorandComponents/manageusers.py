import logging

# import functions
from flask import render_template, url_for, redirect, session, request
from flask import Blueprint
from utils.okta import OktaAdmin
from utils.udp import SESSION_INSTANCE_SETTINGS_KEY, get_app_vertical

from GlobalBehaviorandComponents.validation import is_authenticated, get_userinfo

logger = logging.getLogger(__name__)

# set blueprint
gbac_manageusers_bp = Blueprint('gbac_manageusers_bp', __name__, template_folder='templates', static_folder='static', static_url_path='static')


@gbac_manageusers_bp.route("/manageusers")
@is_authenticated
def gbac_users():
    logger.debug("gbac_users()")
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_group = gbac_get_group_by_name("everyone")
    group_id = user_group["id"]
    group_user_list = okta_admin.get_user_list_by_group_id(group_id)

    return render_template(
        "/manageusers.html",
        templatename=get_app_vertical(),
        user_info=get_userinfo(),
        userlist=group_user_list,
        config=session[SESSION_INSTANCE_SETTINGS_KEY],
        user_group=user_group)


def gbac_get_group_by_name(group_name):
    logger.debug("gbac_get_group_by_name()")
    user_group = None

    if group_name:
        okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
        user_groups = okta_admin.get_groups_by_name(group_name)
        if len(user_groups) > 0:
            # just grab the first one... there should only be one match for now
            logger.debug(user_groups)
            user_group = user_groups[0]

    return user_group


@gbac_manageusers_bp.route("/suspenduser")
@is_authenticated
def gbac_user_suspend():
    logger.debug("gbac_user_suspend()")
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_id = request.args.get('user_id')
    suspend_user = okta_admin.suspend_user(user_id)
    user_info2 = okta_admin.get_user(user_id)

    if not suspend_user:
        message = "User {0} {1} Suspended".format(user_info2['profile']['firstName'], user_info2['profile']['lastName'])
    else:
        message = "Error During Suspension"

    return redirect(url_for("gbac_manageusers_bp.gbac_users", _external="True", _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"], message=message))


@gbac_manageusers_bp.route("/unsuspenduser")
@is_authenticated
def gbac_user_unsuspend():
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_id = request.args.get('user_id')
    unsuspend_user = okta_admin.unsuspend_user(user_id)
    user_info2 = okta_admin.get_user(user_id)

    if not unsuspend_user:
        message = "User {0} {1} Un-Suspended".format(user_info2['profile']['firstName'], user_info2['profile']['lastName'])
    else:
        message = "Error During Un-Suspension"

    return redirect(url_for("gbac_manageusers_bp.gbac_users", _external="True", _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"], message=message))


@gbac_manageusers_bp.route("/resetpassword")
@is_authenticated
def gbac_user_resetpassword():
    logger.debug("gbac_user_resetpassword")
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_id = request.args.get('user_id')
    reset_password = okta_admin.reset_password_for_user(user_id)
    user_info2 = okta_admin.get_user(user_id)

    if not reset_password:
        message = "Password Reset for User {0} {1}".format(user_info2['profile']['firstName'], user_info2['profile']['lastName'])
    else:
        message = "Error During Password Reset"

    return redirect(url_for("gbac_manageusers_bp.gbac_users", _external="True", _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"], message=message))


@gbac_manageusers_bp.route("/manageusercreateupdate")
@is_authenticated
def gbac_create_update_page():
    logger.debug("gbac_create_update_page")
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_id = request.args.get('user_id')
    user_info2 = okta_admin.get_user(user_id)

    return render_template(
        "/manageusercreateupdate.html",
        templatename=get_app_vertical(),
        user_info=get_userinfo(),
        user_info2=user_info2,
        config=session[SESSION_INSTANCE_SETTINGS_KEY])


@gbac_manageusers_bp.route("/createuserinfo", methods=["POST"])
def gbac_user_create():
    logger.debug("gbac_user_create")

    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    email = request.form.get('email')
    login = request.form.get('email')
    mobile_phone = request.form.get('phonenumber')

    user_data = {"profile": {"firstName": first_name, "lastName": last_name, "email": email, "login": login, "mobilePhone": mobile_phone}}

    user_create_response = okta_admin.create_user(user_data)

    if user_create_response:
        message = "User {0} {1} was Created".format(first_name, last_name)
    else:
        message = "Error During Create"

    return redirect(url_for("gbac_manageusers_bp.gbac_users", _external="True", _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"], message=message))


@gbac_manageusers_bp.route("/updateuserinfo", methods=["POST"])
@is_authenticated
def gbac_user_update():
    logger.debug("gbac_user_update")
    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_id = request.form.get('user_id')
    first_name = request.form.get('firstname')
    last_name = request.form.get('lastname')
    email = request.form.get('email')
    mobile_phone = request.form.get('phonenumber')

    user_data = {"profile": {"firstName": first_name, "lastName": last_name, "email": email, "mobilePhone": mobile_phone}}
    user_update_response = okta_admin.update_user(user_id, user_data)

    if user_update_response:
        message = "User {0} {1} was Updated".format(first_name, last_name)
    else:
        message = "Error During Update"

    return redirect(
        url_for(
            "gbac_manageusers_bp.gbac_users",
            _external="True",
            _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"],
            user_id=user_id,
            message=message))
