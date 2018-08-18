import json, re
from bs4 import BeautifulSoup
import networkx as nx
# import matplotlib.pyplot as plt
import math

def loadScalarData(input_file):
    # loads JSON data exported from the Scalar API Explorer tool
    # and parses as a dictionary for further manipulation with Python here

    data_for_output = {}

    with open(input_file, "r", encoding="utf-8") as read_file:
        data = json.load(read_file, strict=False)
        for key in data:
            out_dict = data[key]
            
            # also add the name of the current dictionary to the dcitionary itself and assign to the key 'key'
            # (because we're outputting a list of dictionaries, the key name would be lost otherwise)
            out_dict['key'] = key
            data_for_output[key] = out_dict
    
    return data_for_output

def getTagsAndTaggedNodes(reference_dict, excludeMedia=True):
    # extracts all tags and only the pages that are tagged somewhere in the Scalar book
    # the tags will form the "links" or "edges" in the network
    # (the tags are pretty much ready at this point for the network viz, but we
    # have a few additional steps to go to prepare the nodes)

    tags_for_network_links = []
    tagged_pages_for_network_nodes = []


    for key in reference_dict:
        current_item = reference_dict[key]
        if 'urn:scalar:tag:' in current_item['key']:
            body = current_item['http://www.openannotation.org/ns/hasBody'][0]['value']
            target = current_item['http://www.openannotation.org/ns/hasTarget'][0]['value']

            # ignore tags here that involve media nodes (almost always images)
            if excludeMedia:
                if 'media' in body or 'media' in target:
                    continue
            
            if body not in tagged_pages_for_network_nodes:
                tagged_pages_for_network_nodes.append(body)

            if target not in tagged_pages_for_network_nodes:
                tagged_pages_for_network_nodes.append(target)
            
            tag_dict = {
                'source': body,
                'target': target,
            }
            
            tags_for_network_links.append(tag_dict)
    
    return tags_for_network_links, tagged_pages_for_network_nodes

def parseNodes(scalar_data, pages_identified_in_links):
    # fetch all relevant data about the pages and return as list of nodes
    # including checking for additional page data (text and embedded images)

    list_of_parsed_nodes = []
    for node in pages_identified_in_links:
        current_node_dict = scalar_data[node]
        url = node
        _id = node
        _name = ""
        imageURL = ""
        description = ""
        extraData = "no"

        # look for reference to media
        references = current_node_dict.get("http://purl.org/dc/terms/references")
        mediaReferenced = None
        imageURL = None
        description = None
        if references:
            if "media" in references[0]["value"]:
                mediaReferenced = references[0]["value"]
            # if reference to media found, fetch URL and description from media page
                print("\n")
                content = scalar_data[node]["http://rdfs.org/sioc/ns#content"][0]['value']
                # urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
                # print(urls[0])
                soup = BeautifulSoup(content, "html.parser")
                imageURL = soup.find("a")["href"]
                description = soup.text

                # ceate an abbreviated description (to encourage users to go to Scalar for full description)
                if len(description) > 80:
                    description = description[0:100] + "..."
        
        # when directing the user to the Scalar page via the "url" attribute in the visualization
        # we can ignore the extra version suffix, such as "cafe_central.4" and simply send them to
        # "cafe_central" -- otherwise Scalar may omit the page description (for some reason)
        if url[-2] == '.':
            url = url[0:-2]
        elif url[-3] == '.':
            url = url[0:-3]
        elif url[-4] == '.':
            url = url[0:-4]
        
        try:
            # make sure the node is fetching the name correctly, assign to _name
            _name = current_node_dict['http://purl.org/dc/terms/title'][0]['value']

        except:
            _name = node

        # assemble a dictionary to describe the current node
        node_out = {
            'id' : _id,
            'name' : _name,
            'url' : url,
            'colour':	"#2a2a2a"
        }

        # optional imageURL and description paramaters for the nodes, if the pages include this data
        # will also include an "extraData" parameter to indicate if either attribute exists, for use by
        # the network viz later on
        if imageURL:
            node_out["imageURL"] = imageURL
            extraData = "yes"
        if description:
            node_out["description"] = description
            extraData = "yes"
        node_out["extraData"] = extraData

        list_of_parsed_nodes.append(node_out)

    return list_of_parsed_nodes


def generateBetweennessCentrality(final_list_links, final_list_nodes):
    # use networkx to generate betweennenss centrality for nodes and return as dict

    nodes_for_nx = [node['id'] for node in final_list_nodes]
    edges_for_nx = [(n['source'],n['target']) for n in final_list_links]


    print(edges_for_nx)
    print(nodes_for_nx)
    G=nx.Graph()
    G.add_nodes_from(nodes_for_nx)
    G.add_edges_from(edges_for_nx)
    # nx.draw(G)
    # plt.show()

    return nx.betweenness_centrality(G)


def addBetweennessCentralityToNodes(betweenness_centrality_scores, final_list_links, final_list_nodes):
    # add BC scores as a new parameter, 'betweeness_centrality_score'
    # as an integar between 0 and 100 to use in network viz (as font size, etc.)

    final_output = {}
    final_output['links'] = final_list_links
    final_output['nodes'] = []

    for node in final_list_nodes:
        current_bc_score = betweenness_centrality_scores[node['id']]
        # let's convnert this to a 0 to 100 score, roundng up 
        node['betweenness_centrality_score'] = math.ceil(current_bc_score * 100)
        final_output['nodes'].append(node)
    # print(final_output['nodes'])

    return final_output


def main():

    input_file = "scalar_output.json"
    output_file = "cleaned.json"

    # load Scalar data .json file into Python data
    scalar_data_dict = loadScalarData(input_file)

    # generate final list of links and nodes
    final_links, linked_pages = getTagsAndTaggedNodes(scalar_data_dict)
    final_nodes = parseNodes(scalar_data_dict, linked_pages)

    # generate betweenness centrality scores for nodes using NetworkX 
    betweenness_centrality_scores = generateBetweennessCentrality(final_links, final_nodes)

    # one final step to collect links and nodes (with betweenness-centrality scores added) into a single dictionary
    # (this is assuming this is the most useful way to pass the data to a network visaulization
    # BUT you may wish to modify or rewrite this function if your visualization calls for another way to organize)
    final_output = addBetweennessCentralityToNodes(betweenness_centrality_scores, final_links, final_nodes)

    with open(output_file, "w") as write_file:
        json.dump(final_output, write_file)
        print('clean data successfully written to disk as "cleaned.json"')


if __name__ == "__main__":
    main()