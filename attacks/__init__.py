def inverse_key_schedule(word_size, alpha, beta, k, skipped=0):
    """
    Computes the inverse key schedule for Speck.
    :param word_size: the word size
    :param alpha: the parameter alpha
    :param beta: the parameter beta
    :param k: the array k containing the round keys
    :param skipped: the number of round keys that had been skipped
    :return: the master key
    """
    m = len(k)
    word_size_mod = 2 ** word_size
    l = [0] * skipped
    for i in range(m - 1):
        x = (((k[i] << beta) % word_size_mod) | (k[i] >> (word_size - beta))) ^ k[i + 1]
        x ^= (skipped + i)
        x = (x - k[i]) % word_size_mod
        x = (((x << alpha) % word_size_mod) | (x >> (word_size - alpha)))
        l.append(x)

    # Working backwards until we get to the first k value.
    k = k[0]
    for i in reversed(range(skipped)):
        k ^= l[i + m - 1]
        k = (k >> beta) | ((k << (word_size - beta)) % word_size_mod)
        x = l[i + m - 1] ^ i
        x = (x - k) % word_size_mod
        x = (((x << alpha) % word_size_mod) | (x >> (word_size - alpha)))
        l[i] = x

    return l[m - 2::-1] + [k]
