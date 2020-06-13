# -*- coding: utf-8 -*-
"""
Helper functions for HDF5

Created on Tue Jun  2 12:37:50 2020

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import h5py
import gc
import logging

logger = logging.getLogger(__name__)

def recursive_hdf5_tree(group, lines=[]):
    if isinstance(group, (h5py._hl.group.Group, h5py._hl.files.File)):
        for key, value in group.items():
            lines.append('-{0}: {1}'.format(key, value))
            recursive_hdf5_tree(value, lines)
    elif isinstance(group, h5py._hl.dataset.Dataset):
        for key, value in group.attrs.items():
            lines.append('\t-{0}: {1}'.format(key, value))
    return '\n'.join(lines)

def close_open_files():
    for obj in gc.get_objects():
        if isinstance(obj, h5py.File): 
            msg = 'Found HDF5 File object '
            try:
                msg = '{0}, '.format(obj.filename)
                obj.flush()
                obj.close()
                msg += 'Closed File'
                logger.info(msg)
            except:
                msg += 'File already closed.'
                logger.info(msg)
                
def get_tree(parent):
    """
    Simple function to recursively print the contents of an hdf5 group
    Parameters
    ----------
    parent : :class:`h5py.Group`
        HDF5 (sub-)tree to print

    """
    lines = ['{0}:'.format(parent.name), '=' * 20]
    if not isinstance(parent, (h5py.File, h5py.Group)):
        raise TypeError('Provided object is not a h5py.File or h5py.Group '
                        'object')

    def fancy_print(name, obj):
        #lines.append(name)
        spacing = ' ' * 4 * (name.count('/') + 1)
        group_name = name[name.rfind('/') + 1:]

        
        if isinstance(obj, h5py.Group):
            lines.append('{0}|- Group: {1}'.format(spacing, group_name))
            lines.append('{0}{1}'.format(spacing, 
                                         (len(group_name) + 10) * '-'))
        elif isinstance(obj, h5py.Dataset):
            lines.append('{0}--> Dataset: {1}'.format(spacing, group_name))
            

    #lines.append(parent.name)
    parent.visititems(fancy_print) 
    return '\n'.join(lines)