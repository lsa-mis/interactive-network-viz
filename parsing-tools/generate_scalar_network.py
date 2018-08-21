import json
from bs4 import BeautifulSoup
import networkx as nx
import math

## generate_scalar_network.py takes the JSON output of the Scalar API Explorer tool ( http://scalar.usc.edu/tools/apiexplorer/ )
## for "All of the book's content and relationships" and generates nodes and edges (or "links")
## to be visualized via an interactive network visualization

## this script also generates betweenness centrality scores ( https://en.wikipedia.org/wiki/Betweenness_centrality ) for all nodes/pages
## and includes any image URLs and description text found on nodes/pages

## to read a tutorial on implementing this script, visit https://zoews.github.io/articles/2018-08/custom-scalar-pt1


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
    # extracts all tags and pages that are tagged somewhere in the Scalar book
    # represents each item (tags/pages) as a dictionary
    # and returns a list for each item type

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
    
    # note - you may wish to modify these parameters to include significant data
    # scraping tags is more straightforward, whereas metadata categories/etc. will be specific to your Scalar book

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
        imageURL = None
        description = None
        if references:
            if "media" in references[0]["value"]:
                # if reference to media found, fetch URL and description from media page
                # using BeautifulSoup to parse the HTML descriptions
                content = scalar_data[node]["http://rdfs.org/sioc/ns#content"][0]['value']
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
        # will also include an "extraData" parameter to indicate if either attribute exists
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

    G = nx.Graph()
    G.add_nodes_from(nodes_for_nx)
    G.add_edges_from(edges_for_nx)

    return nx.betweenness_centrality(G)


def addBetweennessCentralityToNodes(betweenness_centrality_scores, final_list_links, final_list_nodes):
    # add BC scores as a new parameter, 'betweeness_centrality_score'
    # as an integar between 0 and 100 to use in network viz (as font size, etc.)

    final_output = {}
    final_output['links'] = final_list_links
    final_output['nodes'] = []

    for node in final_list_nodes:
        current_bc_score = betweenness_centrality_scores[node['id']]
        # convnert this percentage value to an integer between 0 to 100, roundng up 
        node['betweenness_centrality_score'] = math.ceil(current_bc_score * 100)
        final_output['nodes'].append(node)

    return final_output


def main():

    # set filenames for input .json (from Scalar API explorer) and output .json
    input_file = "scalar_output.json"
    output_file = "clean_scalar_data.json"

    # load Scalar data .json file into Python data
    scalar_data_dict = loadScalarData(input_file)

    # generate final list of links and nodes
    final_links, linked_pages = getTagsAndTaggedNodes(scalar_data_dict)
    final_nodes = parseNodes(scalar_data_dict, linked_pages)

    # generate betweenness centrality scores for nodes using NetworkX 
    betweenness_centrality_scores = generateBetweennessCentrality(final_links, final_nodes)

    # one final step to collect links and nodes (with betweenness-centrality scores added) into a single dictionary
    # (you may wish to rewrite this function if your visualization requires a different JSON structure)
    final_output = addBetweennessCentralityToNodes(betweenness_centrality_scores, final_links, final_nodes)

    with open(output_file, "w") as write_file:
        json.dump(final_output, write_file)
        print('clean data successfully written to disk as "clean_scalar_data.json"')


if __name__ == "__main__":
    main()
