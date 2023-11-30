from MSApi.MSApi import MSApi
from MSApi import Assortment, Organization


def get_assortment():
    return list(MSApi.get_object_by_json(product_meta.get_json())(product_meta.get_json()) for product_meta in
                Assortment.gen_list())


def get_assortment_custom_templates():
    return list(Assortment.gen_customtemplates())


def get_organizations():
    return list(Organization.gen_list())