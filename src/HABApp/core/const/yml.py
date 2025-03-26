import ruamel.yaml


yml = ruamel.yaml.YAML()
yml.default_flow_style = False
yml.default_style = False
yml.width = 1000000
yml.allow_unicode = True
yml.sort_base_mapping_type_on_output = False
