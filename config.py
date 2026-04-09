# -*- coding: utf-8 -*-

"""
config.py: default settings for all machine learning models

base: datalake/mock/b.3/ml/config.py

"""


class Config:

     def __init__(self):

          self.generator_path = "."

          # what to predict when there is no output available
          # specifically in generate11 with schemas
          self.null_target = "NULL"

          self.mini10_locales = ["en_US", "en_GB", "de_DE", "fr_CH", "sv_SE", "es_ES", "nn_NO", "it_IT", "nl_NL", "pt_PT"]

          # 10 basic/common locales
          # NOTE: no_NO does not exist, I think it's nn_NO: "Norwegian Nynorsk (Norway)",
          self.locales = ["en_US", "en_GB", "de_DE", "fr_CH", "sv_SE", "es_ES", "nn_NO", "it_IT", "nl_NL", "pt_PT"]

          # SAP List of locales and their dominant locales (60 locales = 71 elements from SAP website less 11 not recognised or causing problems in Babel)
          # src: https://help.sap.com/docs/SAP_BUSINESSOBJECTS_BUSINESS_INTELLIGENCE_PLATFORM/09382741061c40a989fae01e61d54202/46758c5e6e041014910aba7db0e91070.html?version=4.2.4&locale=en-US
          # Removed as causing problems in Babel: tn_ZA, syr_SY, mn_MN, kk_KZ, sq_AL, tr_TR, ru_RU, te_IN, xh_ZA, uk_UA, mk_MK, ta_IN
          self.sap_dominant_locales = ["af_ZA", "ar_SA", "hy_AM", "az_AZ", "eu_ES", "bn_IN", "bs_BA", "bg_BG", "ca_ES", "zh_TW", "zh_CN", "hr_HR", "cs_CZ"
          , "da_DK", "nl_NL", "en_US", "et_EE", "fo_FO", "fi_FI", "fr_FR", "gl_ES", "ka_GE", "de_DE", "el_GR", "gu_IN", "he_IL", "hi_IN", "hu_HU", "is_IS", "id_ID", "it_IT", "ja_JP", "kn_IN"
          , "kok_IN", "ko_KR", "lv_LV", "lt_LT",  "ms_MY", "ml_IN", "mt_MT", "mr_IN", "se_NO", "nb_NO", "nn_NO", "fa_IR", "pl_PL"
          , "pt_BR", "pa_IN", "ro_RO", "sr_BA", "sk_SK", "es_ES", "sw_KE", "sv_SE", "th_TH", "uz_UZ", "vi_VN", "cy_GB", "zu_ZA"
          ]

