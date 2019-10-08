from random import random
from joblib import Parallel, delayed

from .util import oversegmentation, switch_color_space, load_strategy
from .structure import HierarchicalGrouping

def selective_search_one(img, color_space, k, sim_strategy):
    '''
    Selective Search using single diversification strategy
    Parameters
    ----------
        im_orig : ndarray
            Original image
        color_space : string
            Colour Spaces
        k : int
            Threshold parameter for starting regions
        sim_stategy : string
            Combinations of similarity measures
            
    Returns
    -------
        boxes : list
            Bounding boxes of the regions
        priority: list
            Small priority number indicates higher position in the hierarchy
    '''
        
    # Generate starting locations
    img_seg = oversegmentation(img, k)

    # convert RGB image to target color space
    img = switch_color_space(img, color_space)
    
    # Initialze hierarchical grouping
    S = HierarchicalGrouping(img, img_seg, sim_strategy)

    S.build_regions()
    S.build_region_pairs()

    # Start hierarchical grouping
    while not S.is_empty():
        i,j = S.get_highest_similarity()

        S.merge_region(i,j)

        S.remove_similarities(i,j)

        S.calculate_similarity_for_new_region()

    # convert the order by hierarchical priority
    boxes = [x['box'] for x in S.regions.values()][::-1]

    # drop duplicates by maintaining order
    boxes = list(dict.fromkeys(boxes))

    # generate priority for boxes
    priorities = list(range(1, len(boxes)+1))
    
    return boxes, priorities


def selective_search(img, mode='single', random=False):
    """
        Selective Search in Python
    """
    # load selective search strategy
    strategy = load_strategy(mode)
    
    # Excecute selective search in parallel
    vault = Parallel(n_jobs=-1)(delayed(selective_search_one)(img, color, k, sim) for (color, k, sim) in strategy)

    boxes = [x for x,_ in vault]
    priorities = [y for _, y in vault]
    
    boxes = [item for sublist in boxes for item in sublist]    
    priorities = [item for sublist in priorities for item in sublist]
    
    if random:
        # Do pseudo random sorting as in paper
        rand_list = [random() for i in range(len(priorities))]
        priorities = [p * r for p, r in zip(priorities, rand_list)]
        boxes = [b for _, b in sorted(zip(priorities, boxes))]

    # drop duplicates by maintaining order
    boxes = list(dict.fromkeys(boxes))
    
    return boxes