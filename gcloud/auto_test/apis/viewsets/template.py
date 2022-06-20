# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import logging
from django.utils.decorators import method_decorator

from blueapps.account.decorators import login_exempt
from gcloud.common_template.models import CommonTemplate
from gcloud.tasktmpl3.models import TaskTemplate

from ..mixin import BatchDeleteMixin

logger = logging.getLogger("root")


class TemplateViewSet(BatchDeleteMixin):
    pass


@method_decorator(login_exempt, name="dispatch")
class ProjectTemplateViewSet(TemplateViewSet):
    """项目流程模版"""

    queryset = TaskTemplate.objects.all()


@method_decorator(login_exempt, name="dispatch")
class CommonTemplateViewSet(TemplateViewSet):
    """通用流程模版"""

    queryset = CommonTemplate.objects.all()
