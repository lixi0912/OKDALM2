#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, platform, time
from python_tools import dependency_reader
from python_tools import property
import commands, traceback

SNAPSHOT_MAVEN_TYPE = 'snapshot'
RELEASE_MAVEN_TYPE = 'release'

ARTIFACTORY_FILE_NAME = 'artifactory_version.properties'
KEY_MAVEN_TYPE = 'maven_type'
SNAPSHOT_SUFFIX = '-SNAPSHOT'
g_log_result = None
g_debugMode = None
g_to_local = None
g_upgrade = None
g_deploy_all = None
g_in_cur_dir = False
g_force_snap = True
g_reverse = 1


def dump_help():
    print '     +---------------------------------------------------------------------------------------------------------+'
    print '     |    发布module到maven服务器                                                                              |'
    print '     |    usage:                                                                                               |'
    print '     |            python deploy.py [-c] [-l] [-r] [-a] [-d] module_name                                        |'
    print '     |                -c： 可选，只发布当前指定的module（默认同时更新依赖本module的其它module）                |'
    print '     |                -d： mac可选，打印发布信息的log日志                                                      |'
    print '     |                -r： 可选，发布成release版本，默认为snapshot版本                                         |'
    print '     |                -a： 可选，发布artifactory_veresion.properties中配置的所有module                         |'
    print '     |                -i： 可选，--info --stacktrace                                                           |'
    print '     |                -l： 可选，--publishToMavenLocal                                                         |'
    print '     |                -u： 可选，--upgrade                                                                     |'
    print '     |       module_name： 无-a参数时必填，当前发布的module名称                                                |'
    print '     +---------------------------------------------------------------------------------------------------------+'
    sys.exit()


# 获取gradle命令
def get_command():
    plat = platform.system()
    if 'Windows' == plat:
        return 'gradlew '
    # elif 'Darwin' == plat:
    #     return './gradlew '
    # elif 'Linux' == plat:
    #     return './gradlew '
    else:
        return './gradlew ' if g_in_cur_dir else '../gradlew '


# 如果是 debugMode 就显示编译信息
def format_debug_if_need(command_str):
    if g_debugMode:
        return command_str + ' --info --stacktrace --debug'
    else:
        return command_str


def do_deploy_to_maven_local(lib_module_name):
    if not g_to_local:
        return -1
    ## 先编译成 aar
    command_str = '{0} :{1}:clean :{1}:assembleRelease '
    operation = do_exec(command_str, lib_module_name, False)
    if operation != 0:
        command_str = '{0} :{1}:clean :{1}:assemble '
        operation = do_exec(command_str, lib_module_name)

    if operation != 0:
        print "ERROR:artifactory error %d. please check module dependencies" % result
        return operation
    else:
        ## push 到 maven local
        command_str = '{0} :{1}:publishToMavenLocal'
        return do_exec(command_str, lib_module_name)


def do_deploy(lib_module_name, is_reverse):
    print '--------------     [ %s ] deploy: start     ---------------------' % lib_module_name

    deploy_module_name = wrap_module_name(lib_module_name)
    if g_to_local:
        result = do_deploy_to_maven_local(deploy_module_name)
    else:
        command_str = '{0} :{1}:clean :{1}:assembleRelease :{1}:generatePomFileForAarPublication :{1}:artifactoryPublish'
        result = do_exec(command_str, deploy_module_name)
        if result != 0:
            command_str = '{0} :{1}:clean :{1}:assemble :{1}:generatePomFileForAarPublication :{1}:artifactoryPublish'
            result = do_exec(command_str, deploy_module_name)

    if result != 0:
        print "ERROR: artifactory error %d. please check module dependencies" % result
    else:
        deploy_version = get_deploy_version(lib_module_name)
        gradle_version = get_gradle_version(lib_module_name)
        # 如果本次发布的版本号与之前一致，则不升级传递依赖的module版本号
        if gradle_version == deploy_version:
            print 'module %s:%s:%s refreshed' % (group_id, lib_module_name, deploy_version)
            print 'DEPLOY SUCCESS: %s:%s:%s' % (group_id, lib_module_name, deploy_version)
            if is_reverse:
                print '\nNOTE: version no change so skip the reverse deploy version '
            return result
        else:
            # 修改gradle.properties文件中的版本号（=module刚发布成功的版本号=被依赖的版本号）
            gradle_properties.put(gradle_key_prefix + lib_module_name, deploy_version)
            print 'modify gradle.properties: [%s: %s -> %s]' % (
                gradle_key_prefix + lib_module_name, gradle_version, deploy_version)
            print 'DEPLOY SUCCESS: %s:%s:%s' % (group_id, lib_module_name, deploy_version)

        if is_reverse:
            reverse_modules = module_dependencies.get_all_reverse_dependencies(lib_module_name)
            if len(reverse_modules) > 0:
                print 'start deploying reverse dependency modules:'
                print reverse_modules
                success_modules = []
                failed_modules = []
                for m in reverse_modules:
                    version_level_up(m)
                    if do_deploy(m, 0) == 0:
                        success_modules.append(m)
                    else:
                        failed_modules.append(m)
                print 'deploying reverse dependency modules finished.'
                print '\nsuccess_modules: %d' % len(success_modules)
                print success_modules
                print 'failed_modules: %d' % len(failed_modules)
                print failed_modules
            else:
                print 'NOTE: no reverse dependency modules'
        else:
            print 'NOTE: no reverse dependency modules'

    return result


def wrap_module_name(lib_module_name):
    if version_properties.has_key(lib_module_name + "Under"):
        return version_properties.get(lib_module_name + "Under") + ":" + lib_module_name
    else:
        return lib_module_name


def unwrap_module_name(lib_module_name):
    name_array = lib_module_name.split(":")
    if len(name_array) > 0:
        return name_array[1]
    return lib_module_name


def do_exec(command_str, lib_module_name, log_err=True):
    command_str = format_debug_if_need(command_str)
    command = command_str.format(get_command(), lib_module_name)
    print command
    if g_log_result:
        result = os.system(command)
    else:
        result, log = commands.getstatusoutput(command)
        if result != 0 and log_err:
            print log
    return result


# 从release切到snapshot时进行版本升级
def version_level_up(lib_module_name):
    if not g_upgrade:
        return

    # 说明当前需要升级
    # 如果当前 gradle_version 是 snap 就忽略
    gv = get_gradle_version(lib_module_name)
    dv = version_properties.get(lib_module_name)
    print 'NOTE: %s: [%s: %s -> %s]' % ('pre_update', lib_module_name, gv, dv)
    # gv不带-SNAPSHOT后缀，表明已发布到旧版本是release版本
    # 并且当前版本号与 artifactory_version.properties 中设置的发布版本号一致
    # 说明当前到操作是要发布 snapshot 版
    # 也就是当前 deploy 的操作从 release 版切换到 snapshot 版，版本号自动升级
    # 自动升级版本号只是升级一个小版本：最后一位数字（非数字自动忽略），若要升级大版本，可手动修改 artifactory_veresion.properties 中的版本号

    last_int_end = len(dv)
    last_int_start = last_int_end - 1

    while True:
        if last_int_start >= 0 and dv[last_int_start].isdigit():
            if last_int_start > 0:
                last_int_start -= 1
            else:
                break
        elif last_int_start == last_int_end - 1:
            last_int_end = last_int_start
            if last_int_start > 0:
                last_int_start -= 1
            else:
                break
        else:
            last_int_start += 1
            break
    if 0 <= last_int_start < last_int_end:

        last_number = dv[last_int_start:last_int_end]
        upgraded_version_number = str(int(last_number) + 1)

        version = dv[:last_int_start] + upgraded_version_number + dv[last_int_end:]
        version_properties.put(lib_module_name, version)
        print 'NOTE: modify %s: [%s: %s -> %s]' % (
            ARTIFACTORY_FILE_NAME, lib_module_name, dv, version)
    else:
        print 'Error: auto level up %s: [%s: %s] failed!' % (
            ARTIFACTORY_FILE_NAME, lib_module_name, dv)


def rewrite_module_maven_type(lib_module_name):
    maven_key = make_maven_key(lib_module_name)
    cur_maven_type = get_maven_type(maven_key)
    if force_release() and cur_maven_type == SNAPSHOT_MAVEN_TYPE:
        print 'NOTE: modify maven type %s: [%s: %s -> %s]' % (
            ARTIFACTORY_FILE_NAME, maven_key, cur_maven_type, RELEASE_MAVEN_TYPE)
        # 如果当前配置强制升级 -r ，即使 module 是 snap，也更新为 release
        version_properties.put(maven_key, RELEASE_MAVEN_TYPE)
    else:
        # 重写一次版本号
        version_properties.put(maven_key, cur_maven_type)


def force_release():
    return not g_force_snap


def make_maven_key(lib_module_name):
    return lib_module_name + 'MavenType'


def get_maven_type(lib_module_name):
    return version_properties.get(lib_module_name, version_properties.get(
        KEY_MAVEN_TYPE))


def is_snap(lib_module_name):
    return SNAPSHOT_MAVEN_TYPE == get_maven_type(make_maven_key(lib_module_name))


def get_gradle_version(lib_module_name):
    return gradle_properties.get(gradle_key_prefix + lib_module_name)


def get_deploy_version(lib_module_name):
    version = version_properties.get(lib_module_name)
    if is_snap(lib_module_name):
        version += SNAPSHOT_SUFFIX
    return version


def read_modules(sys):
    global g_deploy_all
    global g_to_local
    global g_debugMode
    global g_force_snap
    global g_upgrade
    global g_reverse
    global g_log_result

    index = 1
    arg_len = len(sys.argv)
    if arg_len < 2:
        dump_help()
    else:
        while arg_len > index:
            value = sys.argv[index].strip()
            if value.startswith('-'):
                if value == '-h':
                    dump_help()
                elif value == '-c':
                    g_reverse = 0
                elif value == '-a':
                    g_deploy_all = True
                    g_reverse = 0
                elif value == '-d':
                    g_log_result = True
                elif value == '--r':
                    g_reverse = 1
                elif value == '-r':
                    g_force_snap = None
                elif value == '-i':
                    g_debugMode = True
                elif value == '-l':
                    g_to_local = True
                elif value == '-u':
                    g_upgrade = True
            else:
                break
            index += 1
    result = []
    if not g_deploy_all:
        for i in range(index, arg_len):
            result.append(sys.argv[i])  # 要deploy的module名称
        if len(result) == 0:
            dump_help()

    return result


def project_path():
    global g_in_cur_dir
    if os.path.exists(os.getcwd() + '/gradle.properties'):
        g_in_cur_dir = True
        path = os.path.abspath(os.path.curdir)  # 默认为当前目录
    else:
        path = os.path.abspath('..')  # 默认为当前目录
    return path


### deploy的主方法
### name: 要发布的模块名称
### is_reverse: 是否更新发布（直接/间接）依赖本module的其它module（反向查找依赖module）
def deploy_main(lib_module_name, is_reverse):
    result = -1
    print ''
    if version_properties.has_key(lib_module_name):
        rewrite_module_maven_type(lib_module_name)
        version_level_up(lib_module_name)

        result = do_deploy(lib_module_name, is_reverse)
    else:
        print "\n\t\tDEPLOY SKIP: module \":%s\" is undefined in %s\n" % (
            lib_module_name, ARTIFACTORY_FILE_NAME)
    return result


### 直接调用打球py文件
if __name__ == '__main__':
    modules = read_modules(sys)

    # windows环境执行commands.getstatusoutput(command)时报错
    if platform.system() == 'Windows':
        g_log_result = True

    project_abs_path = project_path()

    gradle_properties = property.parse(os.path.join(project_abs_path, 'gradle.properties'))
    version_properties = property.parse(os.path.join(project_abs_path, ARTIFACTORY_FILE_NAME))

    group_id = gradle_properties.get('maven_groupId')
    gradle_key_prefix = gradle_properties.get('version_prefix')
    module_dependencies = dependency_reader.get_project_dependencies(project_abs_path)

    start = time.time()
    start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))
    print '\n++++++++++++++++++++++++++++++++   deploy start working  (start at: %s)    ++++++++++++++++++++++++++++++++++++++++++' % start_time

    try:
        if g_deploy_all:  # deploy所有在artifactory_version.properties中配置的module
            modules = module_dependencies.sorted_modules

        print 'deploy below modules:'
        print modules
        success = []
        failed = []
        for module in modules:  # 按照依赖关系的顺序进行发布
            if module not in success:
                if deploy_main(module, g_reverse) == 0:
                    success.append(module)
                else:
                    failed.append(module)
            else:
                print "skip success:" + module
        print '\ndeploy finished!'
        print 'success:' + str(len(success))
        print success
        print 'failed:' + str(len(failed))
        print failed

    except Exception, e:
        print traceback.format_exc()

    end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print '++++++++++++++++++++++++++++++++  deploy completed   (end at: %s, cost: %ds) ++++++++++++++++++++++++++++++++++++++++\n' % (
        end_time, time.time() - start)
