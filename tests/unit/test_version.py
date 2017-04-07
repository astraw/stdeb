def test_debianize_pep440():
    from stdeb.util import debianize_version

    assert '1.0~a1' == debianize_version('1.0_a1')
    assert '1.0~dev1' == debianize_version('1.0.dev1')
    assert '1.0~a1~dev1' == debianize_version('1.0.a1.dev1')
    assert '1.0.post1' == debianize_version('1.0.post1')
    assert '1.0~a4.post1' == debianize_version('1.0a4.post1')
    assert '1.0~a4.post1+9.6' == debianize_version('1.0a4.post1+9.6')

    assert '1.0.legacy1' == debianize_version('1.0.LEGACY1')
