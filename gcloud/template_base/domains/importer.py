# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific lan
"""

from django.db import transaction

from .template_manager import TemplateManager
from ..utils import replace_biz_id_value


class TemplateImporter:
    def __init__(self, template_model_cls):
        self.template_model_cls = template_model_cls

    def import_template(self, operator: str, template_data: list, bk_biz_id: int = None) -> dict:
        """
        以 operator 的身份来导入若干个模板

        :param operator: 操作者
        :type operator: str
        :param template_data: [
            {
                "override_template_id": "要覆盖的模板的主键ID",
                "refer_template_id": "要引用的模版的主键ID",
                "name": "模板名",
                "pipeline_tree": "dict, 模板 pipeline tree",
                "description": "模板描述"，
                "template_kwargs": "dict, 模板创建关键字参数",
                "id": "str, 模板临时唯一 ID"
            }
        ]
        :type template_data: list
        :param bk_biz_id: 导入业务ID，公共流程为None
        :type bk_biz_id: int
        :return: [description]
        :rtype: dict
        """
        manager = TemplateManager(template_model_cls=self.template_model_cls)
        import_result = []
        pipeline_id_map = {}
        source_info_map = {}
        with transaction.atomic():
            for td in template_data:
                override_template_id = td["override_template_id"]
                refer_template_id = td["refer_template_id"]
                name = td["name"]
                pipeline_tree = td["pipeline_tree"]
                description = td["description"]

                if bk_biz_id:
                    replace_biz_id_value(pipeline_tree, bk_biz_id)
                replace_result = self._replace_subprocess_template_id(pipeline_tree, pipeline_id_map, source_info_map)
                if not replace_result["result"]:
                    import_result.append(replace_result)
                    continue

                if override_template_id or refer_template_id:
                    template_id = override_template_id or refer_template_id
                    try:
                        template = self.template_model_cls.objects.get(id=template_id)
                    except self.template_model_cls.DoesNotExist as e:
                        import_result.append(
                            {
                                "result": False,
                                "data": "",
                                "message": f"Template does not exist with id {template_id}",
                                "verbose_message": e,
                            }
                        )
                        continue

                if override_template_id:
                    operate_result = manager.update(
                        template=template,
                        editor=operator,
                        name=name,
                        pipeline_tree=pipeline_tree,
                        description=description,
                    )
                    if operate_result["result"]:
                        pipeline_id_map[td["id"]] = operate_result["data"].id
                elif refer_template_id:
                    for key, constant in template.pipeline_tree["constants"].items():
                        source_info_map.setdefault(td["id"], {}).update({key: constant.get("source_info", {})})
                    pipeline_id_map[td["id"]] = refer_template_id
                    operate_result = {"result": True, "data": None, "message": "success", "verbose_message": "success"}
                else:
                    operate_result = manager.create(
                        name=name,
                        creator=operator,
                        pipeline_tree=pipeline_tree,
                        template_kwargs=td["template_kwargs"],
                        description=description,
                    )
                    if operate_result["result"]:
                        pipeline_id_map[td["id"]] = operate_result["data"].id
                import_result.append(operate_result)

        return {"result": True, "data": import_result, "message": "success", "verbose_message": "success"}

    @staticmethod
    def _replace_subprocess_template_id(pipeline_tree: dict, pipeline_id_map: dict, source_map_info: dict) -> dict:
        """
        将模板数据中临时的模板 ID 替换成数据库中模型的主键 ID

        :param pipeline_tree: pipeline tree 模板数据
        :type pipeline_tree: dict
        :param pipeline_id_map: Subprocess 节点中临时 ID 到数据库模型主键 ID 的映射
        :type pipeline_id_map: dict
        :param source_map_info: Subprocess 节点变量的的source_info替换成对应子流程一样的值
        :type source_map_info: dict
        """
        if not pipeline_id_map:
            return {
                "result": True,
                "data": None,
                "message": "pipeline_id_map is empty",
                "verbose_message": "pipeline_id_map is empty",
            }
        for act in pipeline_tree["activities"].values():
            if act["type"] == "SubProcess":
                if act["template_id"] not in pipeline_id_map:
                    return {
                        "result": False,
                        "data": None,
                        "message": "can not find {} in pipeline_id_map".format(act["template_id"]),
                        "verbose_message": "can not find {} in pipeline_id_map: {}".format(
                            act["template_id"], pipeline_id_map
                        ),
                    }
                imported_template_id = act["template_id"]
                act["template_id"] = pipeline_id_map[imported_template_id]
                if imported_template_id in source_map_info:
                    for key, constant in act["constants"].items():
                        constant["source_info"] = source_map_info[imported_template_id].get(key, {})
        return {
            "result": True,
            "data": None,
            "message": "success",
            "verbose_message": "success",
        }
