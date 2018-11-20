# OKDALM2

[![](https://img.shields.io/badge/lastest_version-1.3-orange.svg)](CHANGELOG.md)
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
    <pre>
    upgrade parent version will reverse upgrade his children version
    </pre>
