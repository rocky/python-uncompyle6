# Show off indentation based on source code indentation
# New lines are influenced by source-code new lines
opts = {'highlight':
        True,
        'start_line':
        -1,
        'end_line':
        None, 'a': 1, 'b': 2,
}
x = 5
bar = (1,2,3,4,x,6,7,8,9,
       10,11,12,13,14,15,16,
       17,18)
print(opts, bar)
