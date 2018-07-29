import json

data_for_viz = []
reference_dict = {}
final_list_links = []
final_list_nodes = []
nodes_identified_in_links = []

input_file = "scalar_dump_07_29_2018.json"
output_file = "cleaned.json"

with open(input_file, "r", encoding="utf-8") as read_file:
    data = json.load(read_file, strict=False)
    for key in data:
        out_dict = data[key]
        out_dict['key'] = key
        data_for_viz.append(out_dict)
        reference_dict[key] = out_dict

for item in data_for_viz:
    if 'urn:scalar:tag:' in item['key']:
        body = item['http://www.openannotation.org/ns/hasBody'][0]['value']
        target = item['http://www.openannotation.org/ns/hasTarget'][0]['value']
        if body not in nodes_identified_in_links:
            nodes_identified_in_links.append(body)

        if target not in nodes_identified_in_links:
            nodes_identified_in_links.append(target)
        
        # print('Body = ' + body)
        # print('Target = ' + target + '\n')
        # print(body)
        # print(target)
    
        tag_dict = {
            'source': body,
            'target': target,
        }
        
        final_list_links.append(tag_dict)
print(nodes_identified_in_links)

for node in nodes_identified_in_links:
    current_node_dict = reference_dict[node]
    url = node
    _id = node
    _name = ""

    # get rid of part of URL after period (multiple versions in Scalar)
    if url[-2] == '.':
        url = url[0:-2]
    elif url[-3] == '.':
        url = url[0:-3]
    elif url[-4] == '.':
        url = url[0:-4]

    
    try:
        _name = current_node_dict['http://purl.org/dc/terms/title'][0]['value']
        # print(title)

    except:
        name = node

    node_out = {
        'id' : _id,
        'name' : _name,
        'url' : url,
        'party':	"Labour",
        'colour':	"#2a2a2a"
    }
    print(node_out)

    final_list_nodes.append(node_out)

            # print('no title')
        
        # try:
        #     for ref in item['http://purl.org/dc/terms/references']:
        #         references.append(ref['value'])
        #     # print(references)
        # except:
        #     pass
        #     # print('no references')
        
        # try:
        #    for refBy in item['http://purl.org/dc/terms/isReferencedBy']:
        #        isReferencedBy.append(refBy['value'])               
        #     # print(isReferencedBy)
        # except:
        #     pass
        #     # print('no referenced by')
        
        # # isPriorVersion = False
        # # # try:
        # # #     if '.' in url[-4:]:
        # # #         isPriorVersion = True
        # # # except:
        # # #     pass

        # if not isPriorVersion:
        #     final_out_dict[url] = {
        #         'url': url,
        #         'title': title,
        #         'references': references,
        #         'isReferencedBy': isReferencedBy
        #     }
        #     if len(references) > 0:
        #         print(final_out_dict[url].items())
    
final_output = {}
final_output['links'] = final_list_links
final_output['nodes'] = final_list_nodes

print(final_output['nodes'])


with open(output_file, "w") as write_file:
    json.dump(final_output, write_file)
    print('clean data successfully written to disk as "data_file.json"')