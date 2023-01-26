def get_suffix(word):
    ''' Compute maximum suffix length to match for a given word
        based on its length. Suffix will be at most half the length
    '''
    max_len = 4
    if len(word) // 2 < 4:
        max_len = (len(word) // 2)

    if max_len < 1:
        return ''
    else:
        return f'<par n="suffix{max_len}"' + '/>'
