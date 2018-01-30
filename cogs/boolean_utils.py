"""
discord bot cog that is used for various number utility functions
"""
import discord
from discord.ext import commands

class BoolUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bool(self, ctx, *, exp):
        """Creates truth table from expression using !,*,^,+

        Wrap expression in "quotes" to include spaces in your expression.
        If there are spaces in your expression and it is not properly wrapped,
        then it will not process correctly, if at all.

        Single chars are variables, more than one char in a row is invalid.
        More than one ! in a row is invalid... fight me.
        More than 5 variables is invalid, otherwise the messages would be long.
        """
        await ctx.send(get_bool_table(exp))

def setup(bot):
    """Sets up the cog"""
    bot.add_cog(BoolUtilsCog(bot))

def get_bool_table(exp):
    """Parses a boolean expression and creates a truth table"""
    boolean_exp = BooleanExpr(exp)
    return "```" + boolean_exp.get_truth_table() + "```"

#####################################################################
#####################################################################
#### Class to parse and evaluate boolean expressions ################
#####################################################################
#####################################################################

class BooleanExpr:
    # Expression with whitespace stripped
    orig_exp = "empty"
    # How the expression will be displayed
    disp_exp = "empty"
    # Post-fix version of the original expression
    post_exp = ""
    # Set of all the variables
    var_set = set()
    # Stack needed to verify correctness of expr
    var_stack = []
    # Stack to manage operator precedence
    op_stack = []
    # The formatted truth table to be sent on discord
    result_formatted = ""
    # Flag and message in case an error occurs
    error = False
    error_msg = ""

    # Lists all the valid boolean operators
    boolean_ops = ['+', '^', '*', '!', '~']

    # Defines operator precedence
    prec_dict = {
        '!' : 0, # NOT
        '~' : 0, # NOT alias
        '*' : 1, # AND
        '^' : 2, # XOR
        '+' : 3, # OR
        '(' : 8,
        ')' : 9,
        -1  : 10 # op_stack is empty, skip
    }

    def __init__(self, exp):
        '''Initialize all values'''
        self.var_set.clear()
        self.disp_exp = exp
        self.orig_exp = "".join(exp.split())
        # Get rid of double negatation
        self.orig_exp = self.orig_exp.replace('!!', '')
        self.orig_exp = self.orig_exp.replace('~~', '')
        self.orig_exp = self.orig_exp.replace('~!', '')
        self.orig_exp = self.orig_exp.replace('!~', '')
        self.op_stack[:] = []
        self.var_stack[:] = []
        self.error = False
        self.error_msg = ""
        # Create post-fix expression
        self.process_exp(self.orig_exp)

    ######################################################################
    ####### Parse in-fix expression into post-fix ########################
    ######################################################################

    def process_exp(self, exp):
        """
        Processes an in-fix expression and saves a post-fix version
        of the expression on the class level. The post-fix expression
        is easier to evaluate in code and makes creating the truth
        table more efficient.
        """
        self.post_exp = ""
        # Step through chars of booelean expression
        for char in exp:
            if self.error == True:
                return
            if char == ' ':
                continue
            # Alphas are variables
            elif char.isalpha():
                self.var_set.add(char)
                self.var_stack.append(char)
                self.post_exp += char
            # Start parens
            elif char == '(':
                self.op_stack.append(char)
            # End parens
            elif char == ')':
                # Process all operators until start paren
                while self.get_top(self.op_stack) != '(':
                    self.process_an_op()
                    if self.get_top(self.op_stack) == -1:
                        self.error = True
                        self.error_msg = "Unbalanced paren: )"
                        return
                # Pop start paren
                if self.op_stack:
                    self.op_stack.pop()
            # If the char is a valid operator then process it
            elif self.is_valid_op(char):
                self.process_char(char)
            else:
                # we have found an invalid char
                self.error = True
                self.error_msg = "{} is not a valid symbol!".format(char)
        if self.error == True:
            return
        # Process remaining operators
        while self.op_stack and len(self.var_stack) > 0:
            if self.get_top(self.op_stack) == '(':
                self.error = True
                self.error_msg = "Unbalanced paren: ("
            self.process_an_op()

    def is_valid_op(self, char):
        '''True if char is a valid boolean operator'''
        return char in self.boolean_ops

    def process_char(self, char):
        '''Processes a single operator'''
        # Get the precedence of the operator
        prec = self.prec_dict[char]
        # Process all operators with higher precedence
        # (high precedence is indicated with a lower number, sorry)
        while prec >= self.prec_dict[self.get_top(self.op_stack)]:
            self.process_an_op()
        self.op_stack.append(char)

    def get_top(self, arr):
        '''
        If there are elements in the stack, return the top of the stack,
        else return -1 to signify that the stack is empty
        '''
        if not arr:
            return -1
        return arr[-1]

    def process_an_op(self):
        # I don't know if this would happen...
        if not self.op_stack:
            self.error = True
            self.error_msg = "Op stack is empty while trying to process op"
            return
        # Add operator to postfix expression
        temp = self.get_top(self.op_stack)
        self.op_stack.pop()
        self.post_exp += temp
        # If the operator is unary, then there will be no change in var_stack
        if temp != '!' and temp != '~':
            if len(self.var_stack) < 2:
                self.error = True
                self.error_msg = "Too many operators!"
                return
            self.var_stack.pop()
            self.var_stack.pop()
            self.var_stack.append("NUL")

    ######################################################################
    ####### Process all input permutations using the post-fix expr #######
    ######################################################################

    def process_all_exps(self):
        '''
        Process every possible permutation of inputs. Creates the final
        formatted result by recursively considering every possible
        combination of True and False for every variable and processing
        the postfix expression with those inputs.
        '''
        self.result_formatted = ""
        # Get all variables, sort them to ensure consistent tables between runs
        vars = []
        for elem in self.var_set:
            vars.append(elem)
        vars.sort()
        var_num = 0
        # This dictionary will keep track of the value of each variable
        var_dict = {}
        self.format_header(vars)

        # Begin recursion
        var_dict[vars[var_num]] = False
        self.recurse_through_var(vars, var_dict, var_num + 1)
        var_dict[vars[var_num]] = True
        self.recurse_through_var(vars, var_dict, var_num + 1)

        # Add bottom line of formatted result
        self.result_formatted += "+" + "---+" * len(vars)
        self.result_formatted += "-" * len(self.disp_exp) + "--+\n"

    def recurse_through_var(self, vars, var_dict, depth):
        '''
        Recurse until every variable has been set to True or False, then
        once the recursion depth is equal to the number of variables
        process the expression by passing in the dictionary which is
        keeping track of the value of each variable
        '''
        if depth >= len(self.var_set):
            # Process expression for a single permutation of input
            self.process_single_exp(var_dict, vars)
        else:
            # Continue recursion
            var_dict[vars[depth]] = False
            self.recurse_through_var(vars, var_dict, depth + 1)
            var_dict[vars[depth]] = True
            self.recurse_through_var(vars, var_dict, depth + 1)

    def process_single_exp(self, dict_bool, vars):
        '''
        Processes a post-fix expression with the values of each variable
        stroed in `dict_bool`.
        '''
        post_stack = []
        for char in self.post_exp:
            if char.isalpha():
                # Append value of that variable to the stack
                post_stack.append(dict_bool[char])
            elif char in self.prec_dict:
                # Compute result and add it back to stack
                if char == '!' or char == '~':
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
                    result = bool(one) ^ bool(two)
                    post_stack.append(result)
        # Save result in a formatted fashion, will be single line in table
        self.format_result(post_stack.pop(), dict_bool, vars)

    def format_header(self, vars):
        '''Creates the header to the truth table'''
        self.result_formatted += "+" + "---+" * len(vars)
        self.result_formatted += "-" * len(self.disp_exp) + "--+\n"
        for var in vars:
            self.result_formatted += "| {} ".format(var)
        self.result_formatted += "| {} |\n".format(self.disp_exp)
        self.result_formatted += "+---" * len(vars)
        self.result_formatted += "+" + "-" * len(self.disp_exp) + "--+\n"

    def format_result(self, result, dict_bool, vars):
        '''Creates single line in the truth table'''
        for var in vars:
            booly = int(dict_bool[var])
            self.result_formatted += "| {} ".format(booly)
        res = int(result)
        self.result_formatted += "| {}".format(res)
        self.result_formatted += " " * len(self.disp_exp) + "|\n"

    def valid_vars(self):
        '''False if there are two vars right next to each other'''
        for i in range(1, len(self.orig_exp)):
            if self.orig_exp[i].isalpha() and self.orig_exp[i - 1].isalpha():
                return False
        return True

    def valid_negation(self):
        '''False if operator! is placed incorrectly'''
        not_list = ['!', '~']
        for i in range(1, len(self.orig_exp)):
            if self.orig_exp[i] in not_list and self.orig_exp[i - 1].isalpha():
                self.error_msg = "! should come before a variable, not after."
                return False
            if self.orig_exp[i] in not_list and self.orig_exp[i - 1] == ')':
                self.error_msg = "'!' should not follow a ')'"
                return False
        return True

    def get_truth_table(self):
        '''Returns formatted version of the truth table for a boolean expr'''
        if not self.valid_vars():
            self.error = True
            self.error_msg = "Cannot have two variables in a row..."
        if not self.valid_negation():
            self.error = True
        if self.error == True:
            return "The expression: {}, is invalid!\n{}".format(self.disp_exp,
                                                                self.error_msg)
        if len(set(self.var_set)) > 5:
            return "Too many variables! Will result in spam..."
        # print("Variable set: {}".format(self.var_set))
        # # print(self.op_stack)
        # print("\nIn-fix:   {}".format(self.orig_exp))
        # print("Post-fix: {}".format(self.post_exp))
        self.process_all_exps()
        return self.result_formatted

# Run some basic tests
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

    exp = "A^C+!((A * C)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "A^C)++!(A * C))"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "A^C++!(A * C))"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "ABCD"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "!(x + y)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "(x!y + y)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "(x + y)!"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "(!!x + y)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "(!+!x + y)"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "!(!(!x + y))"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())

    exp = "!   !   !x + y"
    exp_obj = BooleanExpr(exp)
    print(exp_obj.get_truth_table())
