import sys, os, string
import pythoncom
import win32com.client
from util import CheckClean
import traceback

def GenerateAndRunOldStyle():
    import GenTestScripts
    GenTestScripts.GenerateAll()
    try:
        pass #
    finally:
        GenTestScripts.CleanAll()

def CleanGenerated():
    import win32com, shutil
    if os.path.isdir(win32com.__gen_path__):
        print "Deleting files from %s" % (win32com.__gen_path__)
        shutil.rmtree(win32com.__gen_path__)
    import win32com.client.gencache
    win32com.client.gencache.__init__() # Reset

def _test_with_import(capture, module_name, fn_name, desc):
    try:
        mod = __import__(module_name)
    except (ImportError, pythoncom.com_error):
        print "The '%s' test can not be run - failed to import test module" % desc
        return
    capture.capture()
    try:
        func = getattr(mod, fn_name)
        func()
        capture.release()
        print "%s generated %d lines of output" % (desc, capture.get_num_lines_captured())
    except:
        traceback.print_exc()
        capture.release()
        print "***** %s test FAILED after %d lines of output" % (desc, capture.get_num_lines_captured())

unittest_modules = "testIterators".split()

if __name__=='__main__':
    # default to "quick" test.  2==medium, 3==full
    testLevel = 1
    try:
        if len(sys.argv)>1:
            testLevel = int(sys.argv[1])
    except ValueError:
        print "Usage: testall [level], where level is 1, 2 or 3 (default 1, fulltest=3)"

    CleanGenerated()

    import unittest
    testRunner = unittest.TextTestRunner(verbosity=1)
    for mod_name in unittest_modules:
        mod = __import__(mod_name)
        if hasattr(mod, "suite"):
            test = mod.suite()
        else:
            test = unittest.defaultTestLoader.loadTestsFromModule(mod)
        result = testRunner.run(test)
        if not result.wasSuccessful():
            print "*" * 50
            print "Unittest tests failed"
    import win32com.test.util
    capture = win32com.test.util.CaptureWriter()

    if testLevel>1:

        import testMSOffice
        testMSOffice.TestAll()

        import testMSOfficeEvents
        testMSOfficeEvents.test()

        _test_with_import(capture, "testAccess", "test", "MS Access")

        import testExplorer
        testExplorer.TestAll()

        _test_with_import(capture, "testExchange", "test", "MS Exchange")

    _test_with_import(capture, "testStreams", "test", "Streams")
    _test_with_import(capture, "testWMI", "test", "WMI")

    # Execute testPyComTest in its own process so it can play
    # with the Python thread state
    import win32pipe
    data = win32pipe.popen(sys.executable + " testPyComTest.py -q").read()
    data = string.strip(data)
    # lf -> cr/lf
    print string.join(string.split(data, "\n"), "\r\n")

    import errorSemantics
    errorSemantics.test()

    import policySemantics
    policySemantics.TestAll()

    try:
        import testvb
        testvb.TestAll()
    except RuntimeError, why:
        print why


    import testAXScript
    testAXScript.RegisterEngine()
    testAXScript.TestAll()

    # testxslt uses the axscript engine too.
    import testxslt
    testxslt.TestAll()

    import testCollections
    testCollections.TestEnum(1)

    import testDictionary
    testDictionary.TestDict(1)

    import testServers
    testServers.TestAll()

    # Test VBScript and JScript which call back into Python
    cscript_tests = string.split("testInterp.vbs testDictionary.vbs")

    # Note that this test assumes 'Testpys.sct' has been previously registered.
    # To register this test, simply run 'regsvr32.exe Testpys.sct'
    try:
        # First check our test object has actually been installed.
        win32com.client.Dispatch("TestPys.Scriptlet")
        # If it worked, append it to the tests.
        cscript_tests.append("testPyScriptlet.js")
    except pythoncom.error:
        print "Can not test 'Scriptlets' - has Scriptlets been installed and 'Testpys.sct' been registered???"

    for test in cscript_tests:
        cmd_line = "cscript.exe " + test
        print "Running:", cmd_line
        rc = os.system(cmd_line)
        if rc:
            print "***** Test Failed:", cmd_line

    if testLevel>2:

        import testmakepy
        print "Running makepy over every registered typelib..."
        testmakepy.TestAll(0)

    print "Tests completed."
    CheckClean()
    pythoncom.CoUninitialize()
    CleanGenerated()
