<?xml version="1.0"?>
<!-- Dump all politicalParties and politicalGroups as TSV file -->
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xi="http://www.w3.org/2001/XInclude"
  xmlns:tei="http://www.tei-c.org/ns/1.0" 
  xmlns="http://www.tei-c.org/ns/1.0"
  xmlns:et="http://nl.ijs.si/et" 
  exclude-result-prefixes="#all"
  version="2.0">

  <xsl:output method="text"/>
  
  <xsl:template match="text()"/>
  <xsl:template match="/">
    <xsl:text>Country&#9;Role&#9;ID&#9;From&#9;To&#9;Init&#9;Name&#10;</xsl:text>
    <xsl:for-each select="//xi:include">
      <!-- We need "../" as the this XSLT is in Scripts! -->
      <xsl:variable name="href" select="concat('../', @href)"/>
      <xsl:apply-templates select="document($href)//tei:particDesc//tei:org">
	<xsl:with-param name="country" select="replace(@href, '.+ParlaMint-([A-Z]{2}(-[A-Z0-9]{1,3})?).*', '$1')"/>
      </xsl:apply-templates>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template match="tei:org">
    <xsl:param name="country"/>
    <xsl:if test="@role = 'politicalParty' or @role = 'politicalGroup'">
      <xsl:value-of select="$country"/>
      <xsl:text>&#9;</xsl:text>
      <xsl:value-of select="@role"/>
      <xsl:text>&#9;</xsl:text>
      <xsl:value-of select="@xml:id"/>
      <xsl:text>&#9;</xsl:text>
      <xsl:choose>
	<xsl:when test="tei:event[tei:label = 'existence']/@from">
	  <xsl:value-of select="tei:event[tei:label = 'existence']/@from"/>
	</xsl:when>
	<xsl:otherwise>-</xsl:otherwise>
      </xsl:choose>
      <xsl:text>&#9;</xsl:text>
      <xsl:choose>
	<xsl:when test="tei:event[tei:label = 'existence']/@to">
	  <xsl:value-of select="tei:event[tei:label = 'existence']/@to"/>
	</xsl:when>
	<xsl:otherwise>-</xsl:otherwise>
      </xsl:choose>
      <xsl:text>&#9;</xsl:text>
      <xsl:choose>
	<xsl:when test="tei:orgName[@full = 'init']
			[ancestor-or-self::tei:*[@xml:lang][1]/@xml:lang != 'en']">
	  <xsl:value-of select="tei:orgName[@full = 'init']
				[ancestor-or-self::tei:*[@xml:lang][1]/@xml:lang != 'en']"/>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:value-of select="tei:orgName[@full = 'init']"/>
	</xsl:otherwise>
      </xsl:choose>
      <xsl:text>&#9;</xsl:text>
      <xsl:variable name="full-name">
	<xsl:choose>
	  <xsl:when test="tei:orgName[@full = 'yes']
			  [ancestor-or-self::tei:*[@xml:lang][1]/@xml:lang != 'en']">
	    <xsl:value-of select="tei:orgName[@full = 'yes']
				[ancestor-or-self::tei:*[@xml:lang][1]/@xml:lang != 'en']"/>
	  </xsl:when>
	  <xsl:when test="tei:orgName[@full = 'yes']">
	    <xsl:value-of select="tei:orgName[@full = 'yes']"/>
	  </xsl:when>
	  <xsl:otherwise>
	    <xsl:value-of select="tei:orgName[@full = 'init'][1]"/>
	  </xsl:otherwise>
	</xsl:choose>
      </xsl:variable>
      <!-- Some apps don't like quotes in TSV columns, simply delete -->
      <xsl:value-of select="translate($full-name, '&quot;', '')"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
