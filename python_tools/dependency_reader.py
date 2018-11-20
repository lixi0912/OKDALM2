#!/usr/bin/python
# -*- coding: utf-8 -*-

import property
import re
import os
import sys

ARTIFACTORY_FILE_NAME = 'artifactory_version.properties'
# 作为gradle.properties中module的key名称与artifactory_version.properties的差异，如：'version_' 表示： lib_db -> version_lib_db
### 匹配分段写的依赖
linePattern = re.compile(r'(((group)|(name)|(version)|(\w+))\s*\:([^\)]*)){3}')
### 匹配写成一个字符串的依赖
linePattern2 = re.compile(r'[\'\"].*[\'\"]')
artifactIdPattern = re.compile(r'name[^\,]+')


###读取指定工程中的依赖关系
###读取范围：在artifactory_version.properties中声明过的module
###读取内容：groupId为gradle.properties中声明的maven_groupId
###读取结果：字典形式：以module名为key，依赖项数组为value
###读取结果：按照依赖顺序排序的module名称列表
###
### 适配 Compile\Api\Implementation
class Dependency:

    def __init__(self, root_dir):
        gradle_properties = property.parse(os.path.join(root_dir, 'gradle.properties'))
        version_properties = property.parse(os.path.join(root_dir, ARTIFACTORY_FILE_NAME))

        ### 读取在 version_properties 中配置的 modules
        ### 适配如 api 'group:lib:version'
        ### 适配如 api project(':lib')
        module_array = get_deploy_modules(root_dir, version_properties)

        self.root_dir = root_dir
        # 过滤含有build.gradle文件的文件夹（为module）,并解析出build.gradle中对当前工程中各module的依赖项
        self.modules = {}
        ### 匹配当前groupId的依赖项
        self.pattern = re.compile(
            r'.*(ompile|pi|mplementation).*((' + gradle_properties.get('maven_groupId') + ')|(:(' + '|'.join(
                module_array) + '):)).*')
        for file in module_array:
            path = os.path.join(root_dir, file)
            gradle = os.path.join(path, 'build.gradle')
            if os.path.isdir(path) and os.path.isfile(gradle):
                self.modules[file] = read_gradle_dependencies(self.pattern, gradle, module_array)
        self.sorted_modules = self.sort_by_dependency_relationship()

    # 获取直接或间接依赖name的所有module
    def get_all_reverse_dependencies(self, name):
        rev_modules = []
        find_reverse_dependency_module(self.modules, name, rev_modules)
        return rev_modules

    # 按照依赖关系进行排序，被依赖的排在前面先发布
    # 比如 lib2 依赖于 lib, 那么 lib 应该排在前面
    def sort_by_dependency_relationship(self):
        sorted_modules = []

        # 如果只有一项的话，那就没有必要过多的循环了
        if len(self.modules) == 1:
            sorted_modules.append(self.modules.keys()[0])
            return sorted_modules

        m_with_no_deps = []
        # {'lib2': ['lib'],'lib':[],'lib3':['lib2']}
        # 先取出未依赖其它 module 的 module，上例子中为 lib
        for k, v in self.modules.items():
            if len(v) == 0:
                sorted_modules.append(k)
                m_with_no_deps.append(k)

        # 再遍历未依赖的 module
        for m in m_with_no_deps:
            # 上述例子中返回, [lib2,lib3]
            arr = self.get_all_reverse_dependencies(m)  # 计算其被依赖的所有module
            tmp = []
            # 将数组排入序列，确保被依赖的module排在前面
            # 如： ['a', 'b', 'c', 'd']        和       ['A', 'f', 'c', 'e']
            # 排列成： ['a', 'b', 'A', 'f', 'c', 'd', 'e']
            for value in arr:
                if value in sorted_modules:  # 该module出现在序列中，将tmp内的module添加到序列里的value之前
                    if len(tmp) > 0:
                        index = sorted_modules.index(value)
                        for t in tmp:
                            sorted_modules.insert(index, t)
                            index += 1
                        tmp = []
                else:  # 不在序列中，缓存起来
                    tmp.append(value)
            if len(tmp) > 0:
                sorted_modules.extend(tmp)
        return sorted_modules


### 查找所有在 version_properties 中配置的 module
#  通过遍历文件目录名来匹配 module，以及 module 特殊配置了 artifactId 的 module
#  比如 module 对应的目录是 lib, version_properties 中配置 lib 版本及 libArtifactId = specialName
#  那么在后续逆向循环遍历的时候应该需要查找出 specialName 所对应的 module
def get_deploy_modules(root_dir, version_properties):
    module_array = []
    for file in os.listdir(root_dir):
        if version_properties.has_key(file):
            module_array.append(file)
        artifact_key = file + 'ArtifactId'
        if version_properties.has_key(artifact_key):
            module_array.append(version_properties.get(artifact_key))
    return module_array


### 读取 build.gradle 中配置的（当前工程中的）依赖项
# 当前的 module 需要配置在 artifactory_version.properties 中，才可以被匹配出
# 比如 project --- lib
#             ┗--- lib2
# 在 lib2 dependencies 中依赖了 lib, 那么此处将返回 lib，无关的依赖不会被返回
def read_gradle_dependencies(pattern, gradle, module_array):
    try:
        pro_file = open(gradle, 'r')
        list = []
        annotation = None
        for line in pro_file:
            line = line.strip()
            if annotation:
                annotation = line.endswith('*/')
            elif line.startswith('/*'):
                annotation = True
            else:
                if pattern.search(line) and not line.startswith('//'):
                    name = read_dependency_line(line)
                    if name != '' and name in module_array and name not in list:
                        list.append(name)
    except Exception, e:
        raise e
    else:
        pro_file.close()
        return list


### 读取依赖项的module名称
def read_dependency_line(line):
    sep = None
    if ',' in line:  # 类似于： compile group:maven_groupId, name:'lib_module_c', version: lib_module_c
        sep = True
        p = linePattern
    else:
        p = linePattern2

    match = p.search(line)
    if match:
        # 去除引号
        line = re.sub(r'[\'\"]', '', match.group())
        # 截取module名称
        if sep:
            match = artifactIdPattern.search(line)
            if match:
                return match.group().split(':')[1].strip()
        else:
            return line.split(':')[1].strip()
    else:
        return ''

### 反向查找指定module的依赖（直接和间接依赖该module的module）
# 如 lib:[]  lib3:[lib2]  lib2:[lib]
# 此处 name = lib, 那么 rev_modules:[lib2]
#      name = lib2, 那么 rev_modules:[lib2,lib3]
# 如 name = lib，不在比较 lib:[] 内的依赖项
# name 对应的 module，位于遍历 module 依赖项数组中时，加入到逆向查询依赖的模块数组
def find_reverse_dependency_module(modules, name, rev_modules):
    for module_name in modules:
        if module_name != name and name in modules[module_name]:
            if module_name not in rev_modules:
                rev_modules.append(module_name)
            find_reverse_dependency_module(modules, module_name, rev_modules)


# 读取工程中的依赖关系
def get_project_dependencies(root_dir):
    return Dependency(root_dir)


# 在工程根目录执行以下代码，打印出当前工程下的依赖关系：
# python python_tools/dependency_reader.py
if __name__ == '__main__':
    project_abs_path = os.path.abspath(os.curdir)  # 默认为当前目录
    if len(sys.argv) > 1:
        project_abs_path = os.path.join(project_abs_path, sys.argv[1])
    dependency = get_project_dependencies(project_abs_path)
    module_dependencies = dependency.modules
    for key in module_dependencies:
        print "module:" + key
        print module_dependencies[key]
        print ''

    print '----------------------------------------------------'
    sorted = dependency.sorted_modules
    print 'sorted modules:'
    print sorted
