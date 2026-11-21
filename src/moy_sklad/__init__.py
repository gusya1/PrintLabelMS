from MSApi import Assortment, Organization


def get_assortment():
    return list(Assortment.gen_list())


def get_assortment_custom_templates():
    return list(Assortment.gen_customtemplates())


def get_organizations():
    return list(Organization.gen_list())