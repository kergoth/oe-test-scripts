import contextlib
import dot
import errno
import glob
import os
import sh
import shutil
import signal
import sys


class Terminate(BaseException):
    pass


def sigterm_exception(signum, stackframe):
    raise Terminate()


def remove(*files):
    """Remove the specified files or directories"""
    for f in files:
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.unlink(f)


@contextlib.contextmanager
def status(message):
    """Show the user what we're doing, and whether we succeed"""
    sys.stdout.write('{}..'.format(message))
    sys.stdout.flush()
    try:
        yield
    except KeyboardInterrupt:
        sys.stdout.write('.interrupted\n')
        raise
    except Terminate:
        sys.stdout.write('.terminated\n')
        raise
    except BaseException:
        sys.stdout.write('.failed\n')
        raise
    sys.stdout.write('.done\n')


def run(cmd, *args, **kwargs):
    """Run a process, and kill the processes when the user ^C's or terminates"""
    cmdobj = getattr(sh, cmd)
    process = cmdobj(*args, _in='/dev/null', _bg=True, **kwargs)
    sid = os.getsid(process.pid)
    try:
        process.wait()
    except BaseException:
        try:
            os.kill(sid, signal.SIGTERM)
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                return process.stdout
            sys.stderr.write("error killing child processes")
        raise
    return process.stdout


def bitbake(*args, **kwargs):
    """Run bitbake, and kill the processes when the user ^C's or terminates"""
    return run('bitbake', *args, **kwargs)


def dot_to_recipes(dotfile, target, default_task='do_build',
                   build_task='do_populate_sysroot'):
    """Given a .dot file, flatten the graph, limit to execution of build_task, and return a list of these recipes in this order"""
    # Get dependency information
    depends = dot.parse_depends(dotfile)

    # Flatten into a list of recipes
    depend_list = dot.get_all_depends(depends, '%s.%s' % (target, default_task))

    recipes = list(node[0] for node in depend_list if node[1] == build_task)
    return recipes


def ordered_recipelist(target):
    """Run bitbake -g and generate a recipe list in build order for the target"""
    bitbake("-g", target)
    try:
        recipe_list = dot_to_recipes('task-depends.dot', target)
    finally:
        remove(*glob.glob('*.dot'))
        remove('pn-buildlist')

    recipe_list = filter(lambda r: r != target, recipe_list)
    recipe_list.append(target)
    return recipe_list


def get_bitbake_env(recipe=None):
    """Run bitbake -e and return the output as a dictionary"""
    if recipe:
        env_output = bitbake("-e", recipe).splitlines()
    else:
        env_output = bitbake("-e").splitlines()

    # Filter out comments
    env_output = (l for l in env_output if not l.startswith('#'))

    # Split up variables and values into a dictionary
    env_dict = {}
    for line in env_output:
        line = line.rstrip()
        try:
            var, value = line.split('=', 1)
        except ValueError:
            continue
        env_dict[var] = value[1:-1]
    return env_dict


def for_each_recipe(target='core-image-base', excludetarget='pseudo-native'):
    excluded = set()
    if excludetarget:
        with status('Determining recipes to exclude'):
            excluded |= set(ordered_recipelist(excludetarget))

    with status('Extracting ASSUME_PROVIDED from bitbake environment'):
        env = get_bitbake_env()
        excluded |= set(env['ASSUME_PROVIDED'].split())

    recipes_to_build = ordered_recipelist(target)
    for recipe in recipes_to_build:
        if recipe in excluded:
            continue
        yield recipe


def rebuild_recipes(target='core-image-base', excludetarget='pseudo-native',
                    clean=True):
    """Determine what recipes are built to build the target, excluding the
    recipes built to build the excludetarget, then cleans and rebuilds each
    recipe, one by one"""

    for recipe in for_each_recipe(target, excludetarget):
        if clean:
            with status('Cleaning {}'.format(recipe)):
                bitbake('-c', 'cleansstate', recipe)

        with status('Rebuilding {}'.format(recipe)):
            bitbake(recipe)


def run_main(mainfunc, args):
    signal.signal(signal.SIGTERM, sigterm_exception)
    try:
        return mainfunc(args)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
    except Terminate:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
