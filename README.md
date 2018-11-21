# OKDALM2

[![GitHub release](https://img.shields.io/github/release/lixi0912/OKDALM2.svg)](https://github.com/lixi0912/OKDALM2/releases/latest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![ForkfromOKDALM](https://img.shields.io/badge/base-OKDALM-green.svg)](https://github.com/luckybilly/OKDALM)

## Usage
### Import

- terminal
    - `git submodule add https://github.com/lixi0912/OKDALM2 deploy`
- build.gradle (root)
    - apply from: "deploy/artifactory.gradle"        
    - classpath "org.jfrog.buildinfo:build-info-extractor-gradle:4.7.5"
- copy artifactory_version.properties to root_project dir

### Optional
- special pom dependencies configuration (default using deploy/pom.properties)
  - copy pom.properties to root_project dir
  
- gradle.properties (root) add maven account info
  <pre>
  maven_groupId=your.group.id
  artifactory_user=admin
  artifactory_password=password
  artifactory_contextUrl=http://localhost:8081/artifactory
  artifactory_snapshot_repoKey=libs-snapshot-local
  artifactory_release_repoKey=libs-release-local
  version_prefix=
  </pre>
  
### Publish
- open Terminal
  - python deploy/deploy.py [-c] [-l] [-a] [-u] [-r] [-d] [-i] module_name
      - [-l] publish to local maven
      - [-u] force upgrade
      - [-a] deploy all
      - [-c] deploy module by module_name
      - [-r] force release 
      - [-d] print log
      - [-i] build with --info --stacktrace 

### Future

 - [ x ] ~~auto update dependency version~~
    <pre>
    use compile "your.group.id:parent-lib:$parent-lib" instead
    </pre>

 - [ ] child version depends on parent version
    <pre>
    artifactory_version.properties
        children-lib = $parent-lib
    </pre>
