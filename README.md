# OKDALM2

[![](https://img.shields.io/badge/lastest_version-1.3-orange.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![ForkfromOKDALM](https://img.shields.io/badge/base-OKDALM-green.svg)](https://github.com/luckybilly/OKDALM)

## Usage In SubModule

- git submodule add https://github.com/lixi0912/OKDALM2 deploy
- root/build.gradle
    - add apply from: "deploy/artifactory.gradle"        
    - add classpath "org.jfrog.buildinfo:build-info-extractor-gradle:4.7.5"
- root/gradle.properties add maven account info
        <pre>
        maven_groupId=your.group.id
        artifactory_user=admin
        artifactory_password=password
        artifactory_contextUrl=http://localhost:8081/artifactory
        artifactory_snapshot_repoKey=libs-snapshot-local
        artifactory_release_repoKey=libs-release-local
        version_prefix=
        </pre>
- copy artifactory_version.properties to root_project dir
- root/settings.gradle include 'deploy'
- config special configuration (default deploy/pom.properties)
  - copy pom.properties to root_project dir
  - add configuration
- Terminal
  - cd deploy
  - python deploy.py [-c] [-l] [-a] [-u] [-r] module_name
      - [-l] publish to local maven
      - [-u] force upgrade
      - [-a] deploy all
      - [-c] deploy module by module_name
      - [-r] force release 
      - [-d] print log
      - [-i] build with --info --stacktrace 

### Future

 - [ ] auto update dependency version