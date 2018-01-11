class BooleanExpr:
    orig_exp = "empty"
    post_exp = ""
    var_set = set()
    op_stack = []
    result_formatted = ""

    prec_dict = {
        '!' : 0, # NOT
        '*' : 1, # AND
        '^' : 2, # XOR
        '+' : 3, # OR
    }

    def __init__(self, exp):
        self.var_set.clear()
        self.op_stack[:] = []
        self.orig_exp = exp
        self.process_exp(self.orig_exp)

    def process_exp(self, exp):
        """
        Processes an in-fix expression and saves a post-fix version
        of the expression on the class level. The post-fix expression
        is easier to evaluate in code, thus leading to greater efficiency.
        """
        self.post_exp = ""
        # Step through chars of booelean expression
        for char in exp:
            if char == ' ':
                continue
            # Alphas are variables
            elif char.isalpha():
                self.var_set.add(char)
                self.post_exp += char
            elif char == '(':
                self.op_stack.append(char)
            elif char == ')':
                while self.op_stack[-1] != '(':
                    self.process_an_op()
                self.op_stack.pop()
            elif char == '+':
                while self.op_stack and (self.op_stack[-1] == '+'   \
                        or self.op_stack[-1] == '!'                 \
                        or self.op_stack[-1] == '*'                 \
                        or self.op_stack[-1] == '^'):
                    self.process_an_op()
                self.op_stack.append(char)
            elif char == '^':
                while self.op_stack and (self.op_stack[-1] == '!'   \
                        or self.op_stack[-1] == '*'                 \
                        or self.op_stack[-1] == '^'):
                    self.process_an_op()
                self.op_stack.append(char)
            elif char == '*':
                while self.op_stack and (self.op_stack[-1] == '!'   \
                        or self.op_stack[-1] == '*'):
                    self.process_an_op()
                self.op_stack.append(char)
            elif char == '!':
                while self.op_stack and self.op_stack[-1] == '!':
                    self.process_an_op()
                self.op_stack.append(char)
        while self.op_stack:
            self.process_an_op()

    def process_an_op(self):
        # print("Processing: {}".format(self.op_stack[-1]))
        self.post_exp += self.op_stack[-1]
        self.op_stack.pop()

    def process_all_exps(self):
        self.result_formatted = ""
        vars = []
        for elem in self.var_set:
            vars.append(elem)
        vars.sort()
        var_num = 0
        var_dict = {}
        self.format_header(vars)

        var_dict[vars[var_num]] = False
        self.recurse_through_var(vars, var_dict, var_num + 1)
        var_dict[vars[var_num]] = True
        self.recurse_through_var(vars, var_dict, var_num + 1)

    def recurse_through_var(self, vars, var_dict, depth):
        if depth >= len(self.var_set):
            self.process_single_exp(var_dict, vars)
        else:
            var_dict[vars[depth]] = False
            self.recurse_through_var(vars, var_dict, depth + 1)
            var_dict[vars[depth]] = True
            self.recurse_through_var(vars, var_dict, depth + 1)

    def process_single_exp(self, dict_bool, vars):
        # print(dict_bool)
        post_stack = []
        for char in self.post_exp:
            # print(post_stack)
            if char.isalpha():
                post_stack.append(dict_bool[char])
            elif char in self.prec_dict:
                if char == '!':
                    one = not post_stack.pop()
                    post_stack.append(one)
                if char == '*':
                    one = post_stack.pop() 
                    two = post_stack.pop()
                    result = one and two
                    post_stack.append(result)
                if char == '+':
                    one = post_stack.pop() 
                    two = post_stack.pop()
                    result = one or two
                    post_stack.append(result)
                if char == '^':
                    one = post_stack.pop() 
                    two = post_stack.pop()
                    result = one and not two or two and not one
                    post_stack.append(result)
        self.format_result(post_stack.pop(), dict_bool, vars)
        # print("Single result: {}".format(post_stack.pop()))

    def format_header(self, vars):
        self.result_formatted += "----" * len(vars)
        self.result_formatted += "-" * len(self.orig_exp) + "----\n"
        for var in vars:
            self.result_formatted += "| {} ".format(var)
        self.result_formatted += "| {} |\n".format(self.orig_exp) 
        self.result_formatted += "----" * len(vars)
        self.result_formatted += "-" * len(self.orig_exp) + "----\n"

    def format_result(self, result, dict_bool, vars):
        for var in vars:
            if dict_bool[var] == True:
                booly = 1
            else:
                booly = 0
            self.result_formatted += "| {} ".format(booly)
        self.result_formatted += "| {}\n".format(result)

    def get_truth_table(self):
        if len(set(self.var_set)) > 5:
            return "Too many variables! Will result in spam..."
        # print("Variable set: {}".format(self.var_set))
        # # print(self.op_stack)
        # print("In-fix:   {}".format(self.orig_exp))
        # print("Post-fix: {}".format(self.post_exp))
        self.process_all_exps()
        return self.result_formatted

def get_top(arr):
    if not arr:
        return -1
    return arr.pop()

if __name__ == '__main__':
    exp = "A+C"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())
    exp = "A*C"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())
    exp = "A^C+!(A * C)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "A+!B*C+!A*C*!D"
    exp_obj_2 = BooleanExpr(exp)
    print(exp_obj_2.get_truth_table())
    exp = "A^C++!(A * C)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())
